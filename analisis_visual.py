"""Consulta SQLite y genera un diagrama H–R de Gaia DR3."""

import sqlite3
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt

# Crea la conexión con la base de datos
conexion = sqlite3.connect("resultados/datos_mision.db")

# Consulta los datos de interés
consulta = "SELECT color_bp_rp, mag_g_absoluta FROM estrellas_gaia;"

# Pandas ejecuta la consulta y guarda el resultado en un DataFrame.
datos = pd.read_sql_query(consulta, conexion)

# Cierra la conexión con la base de datos
conexion.close()

print("Datos extraídos de la base de datos:")
print(datos.head())

# Conserva el rango físicamente útil antes de calcular la densidad.
visibles = datos[
    datos["color_bp_rp"].between(-0.5, 4)
    & datos["mag_g_absoluta"].between(-5, 15)
].copy()

# Regiones aproximadas para identificar poblaciones en el diagrama. No son
# clasificaciones espectroscópicas de estrellas individuales.
x = visibles["color_bp_rp"]
y = visibles["mag_g_absoluta"]
mascara_gigantes = x.between(0.9, 3.2) & (y < 3.0) & (y > -5)
mascara_secuencia = (
    x.between(-0.4, 3.3)
    & (y >= 2.7 * x + 0.8)
    & (y <= 3.8 * x + 4.0)
    & ~mascara_gigantes
)

fig, ax = plt.subplots(figsize=(10, 8))
densidad = ax.hexbin(
    x, y, C=x, reduce_C_function=np.mean, gridsize=180, mincnt=1,
    cmap="coolwarm", vmin=-0.5, vmax=4, linewidths=0, alpha=0.65,
)
ax.scatter(x[mascara_secuencia], y[mascara_secuencia],
           c=x[mascara_secuencia], cmap="coolwarm", vmin=-0.5, vmax=4,
           s=2, alpha=0.22, linewidths=0,
           label="Secuencia principal")
ax.scatter(x[mascara_gigantes], y[mascara_gigantes],
           c=x[mascara_gigantes], cmap="coolwarm", vmin=-0.5, vmax=4,
           s=7, alpha=0.55, edgecolors="#9e2522", linewidths=0.25,
           label="Gigantes rojas")

ax.annotate("Secuencia principal", xy=(1.45, 7.3), xytext=(2.35, 5.2),
            arrowprops={"arrowstyle": "->", "color": "#2474b5"},
            color="#155489", fontsize=11, weight="bold")
ax.annotate("Rama de gigantes rojas", xy=(1.45, 1.1), xytext=(2.15, -2.5),
            arrowprops={"arrowstyle": "->", "color": "#b52d29"},
            color="#9e2522", fontsize=11, weight="bold")

ax.set_xlim(-0.5, 4)
ax.set_ylim(15, -5)

ax.set_xlabel("Índice de color Gaia BP − RP [mag]  (azul → rojo)")
ax.set_ylabel("Magnitud absoluta G [mag]  (más luminosas arriba)")
ax.set_title("Diagrama Hertzsprung–Russell — Gaia DR3")
fig.colorbar(densidad, ax=ax, label="Índice de color BP − RP [mag]")
ax.legend(loc="lower right", markerscale=4)

ax.grid(alpha=0.2)
plt.tight_layout()
plt.savefig("resultados/resultado.png", dpi=180)

plt.show()

print("Imagen resultados/resultado.png generada con éxito")
