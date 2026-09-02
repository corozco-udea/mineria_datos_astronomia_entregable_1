import sqlite3
import sys
from pathlib import Path

import numpy as np
import pandas as pd

CSV_PREDETERMINADO = "resultados/gaia_dr3_crudo.csv"
DB = "resultados/datos_mision.db"

# Determina si el CSV se envió como argumento al comando de ejecución y existe
ruta = Path(sys.argv[1] if len(sys.argv) > 1 else CSV_PREDETERMINADO)

if not ruta.is_file():
    raise FileNotFoundError(f"No se encontró {ruta}. Ejecuta primero pipeline.sh")

# Normaliza los campos que vienen del CVS a camel_case para que tengan el formato esperado en la base
datos = pd.read_csv(ruta).rename(columns={
    "Source": "source_id", "Plx": "paralaje", "Gmag": "mag_g",
    "BP-RP": "color_bp_rp", "e_Plx": "error_paralaje",
})

# Parsea los campos a número
columnas = ["paralaje", "mag_g", "color_bp_rp"]
if "error_paralaje" in datos.columns:
    columnas.append("error_paralaje")
for columna in columnas:
    datos[columna] = pd.to_numeric(datos[columna], errors="coerce")

# Limpia campos vacíos, duplicados y calcula la magnitud absoluta que espera el diagrama HR
datos = datos.dropna(subset=["source_id", "paralaje", "mag_g", "color_bp_rp"])
datos = datos[datos.paralaje > 0]
datos = datos.drop_duplicates(subset="source_id").copy()

# La inversión del paralaje solo produce distancias fiables cuando su
# señal/ruido es suficientemente alta. Gaia recomienda no interpretar como
# precisas las distancias obtenidas de paralajes muy inciertos.
if "error_paralaje" in datos.columns:
    datos = datos.dropna(subset=["error_paralaje"])
    datos = datos[datos.error_paralaje > 0].copy()
    datos["snr_paralaje"] = datos.paralaje / datos.error_paralaje
    datos = datos[datos.snr_paralaje >= 10].copy()
else:
    # Compatibilidad con descargas antiguas que no incluían e_Plx. Este filtro
    # es conservador, pero no reemplaza el criterio de señal/ruido.
    print("Advertencia: el CSV no contiene e_Plx; se usa Plx >= 1 mas.")
    datos = datos[datos.paralaje >= 1].copy()

datos["mag_g_absoluta"] = datos.mag_g + 5 * np.log10(datos.paralaje) - 10
datos_db = datos[["source_id", "color_bp_rp", "mag_g_absoluta"]]

# Crea la conexión a la base
conexion = sqlite3.connect(DB)
cursor = conexion.cursor()

# Crea la tabla desde cero
cursor.execute("DROP TABLE IF EXISTS estrellas_gaia")
cursor.execute("""CREATE TABLE estrellas_gaia (source_id INTEGER,color_bp_rp REAL,mag_g_absoluta REAL)""")

# Construye los registros que se insertarán en la base de datos
registros = [
    (int(fila.source_id), float(fila.color_bp_rp), float(fila.mag_g_absoluta))
    for fila in datos_db.itertuples(index=False)
]

# Inserta los datos en bulk
cursor.executemany("""INSERT INTO estrellas_gaia (source_id, color_bp_rp, mag_g_absoluta) VALUES (?, ?, ?)""", registros)

# Sincroniza cambios con la base y cierra la conexión
conexion.commit()
conexion.close()

print(f"Base creada: {DB} ({len(datos_db):,} estrellas limpias)")
