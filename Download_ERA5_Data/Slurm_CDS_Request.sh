#!/usr/bin/env bash
#SBATCH --job-name=cds_era5
#SBATCH --nodelist=atlantis
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=1
#SBATCH --time=90:00:00

#USAGE: sbatch Slurm_CDS_Request.sh 2021-01-01 2021-01-31 ../ERA5/2022/

set -euo pipefail

if [[ $# -ne 3 ]]; then
  echo "Uso: sbatch submit_CDS_Enterprise.sh FECHA_INICIAL FECHA_FINAL RUTA"
  echo "Ejemplo: sbatch submit_CDS_Enterprise.sh 2021-01-01 2021-01-31 ../ERA5/2021/"
  exit 1
fi

FECHA_INICIAL="$1"
FECHA_FINAL="$2"
RUTA="$3"

PYTHON_BIN=$PYTHON
SCRIPT_DIR="/exports/jorgeeiras/EULERIAN_TRACERS/MWDA/1_Download_ERA-5/Descarga_v2/"
PY_SCRIPT="$SCRIPT_DIR/CDS_Request_MWDA_24h.py"

mkdir -p logs
mkdir -p "$RUTA"

echo "========================================"
echo "Job ID       : ${SLURM_JOB_ID:-N/A}"
echo "Nodo         : ${SLURMD_NODENAME:-N/A}"
echo "Inicio       : $(date)"
echo "Fecha ini    : $FECHA_INICIAL"
echo "Fecha fin    : $FECHA_FINAL"
echo "Ruta destino : $RUTA"
echo "Script       : $PY_SCRIPT"
echo "========================================"

"$PYTHON_BIN" "$PY_SCRIPT" "$FECHA_INICIAL" "$FECHA_FINAL" "$RUTA"

echo "Fin: $(date)"
