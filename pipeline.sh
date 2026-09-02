#!/usr/bin/env bash

readonly CSV="resultados/gaia_dr3_crudo.csv"
readonly URL='https://tapvizier.cds.unistra.fr/TAPVizieR/tap/sync'
readonly CONSULTA='request=doQuery&lang=ADQL&format=csv&query=SELECT+TOP+50000+Source%2CPlx%2Ce_Plx%2CGmag%2C%22BP-RP%22+FROM+%22I%2F355%2Fgaiadr3%22'


echo "Elimina la carpeta de resultados antes de ejecutar el pipeline"
rm -rf resultados

echo "Crea una carpeta para almacenar los resultados"
mkdir -p resultados

echo "Descarga una muestra de Gaia DR3"
wget --post-data="$CONSULTA" --output-document="$CSV" "$URL"

echo "Limpieza de datos y creación de la base de datos local..."
python3 constructor_db.py "$CSV"

echo "Cálculos matemáticos y creación del diagrama HR..."
python3 analisis_visual.py

echo "Fin de la ejecución"
