#!/home/jorge/miniconda3/bin/python

# @Author: J. Eiras-Barca 2026
# USAGE: python CDS_Request_MWDA_24h.py 2022-01-01 2022-01-10 ../ERA5/2022

import argparse
import subprocess
from pathlib import Path
from datetime import datetime, timedelta
import cdsapi

HOURS = [
    '00:00:00', '03:00:00', '06:00:00', '09:00:00',
    '12:00:00', '15:00:00', '18:00:00', '21:00:00'
]
STEP_LABELS = ['00', '03', '06', '09', '12', '15', '18', '21']


def retrieve_daily(date_str: str, outdir: Path):
    c = cdsapi.Client()
    ymd = date_str.replace('-', '')
    outdir.mkdir(parents=True, exist_ok=True)

    target_ml = outdir / f"ml_{ymd}_77_130_131_132.nc"
    if not target_ml.exists():
        c.retrieve(
            'reanalysis-era5-complete',
            {
                'class': 'ea',
                'date': date_str,
                'expver': '1',
                'levtype': 'ml',
                'levelist': '40/to/137',
                'param': '77/130/131/132',
                'stream': 'oper',
                'time': HOURS,
                'type': 'an',
                'grid': '1.0/1.0',
                'format': 'netcdf',
            },
            str(target_ml)
        )

    target_sfc = outdir / f"B{ymd}_sp.nc"
    if not target_sfc.exists():
        c.retrieve(
            'reanalysis-era5-complete',
            {
                'class': 'ea',
                'date': date_str,
                'expver': '1',
                'levtype': 'sfc',
                'param': '129.128/134.128',
                'stream': 'oper',
                'time': HOURS,
                'type': 'an',
                'grid': '1.0/1.0',
                'format': 'netcdf',
            },
            str(target_sfc)
        )

    return target_ml, target_sfc


def split_and_verify(daily_file: Path, prefix: Path, labels):
    parent = prefix.parent
    stem = prefix.name

    # Borra restos previos de ese día para evitar mezclas
    for hh in labels:
        f = parent / f"{stem}{hh}.nc"
        if f.exists():
            f.unlink()

    subprocess.run(
        ['cdo', '-O', 'splithour', str(daily_file), str(prefix)],
        check=True
    )

    # Verifica que CDO haya generado exactamente los ficheros esperados
    missing = []
    for hh in labels:
        f = parent / f"{stem}{hh}.nc"
        if not f.exists():
            missing.append(f)

    if missing:
        missing_str = "\n".join(str(f) for f in missing)
        raise FileNotFoundError(f"Faltan archivos tras splithour:\n{missing_str}")


def process_day(date_obj, outdir: Path):
    date_str = date_obj.strftime('%Y-%m-%d')
    ymd = date_obj.strftime('%Y%m%d')

    print(f"Procesando día: {date_str}", flush=True)

    ml_daily, sfc_daily = retrieve_daily(date_str, outdir)

    split_and_verify(
        ml_daily,
        outdir / f"ml_{ymd}_77_130_131_132_",
        STEP_LABELS,
    )
    split_and_verify(
        sfc_daily,
        outdir / f"B{ymd}_sp_",
        STEP_LABELS,
    )

    if ml_daily.exists():
        ml_daily.unlink()
    if sfc_daily.exists():
        sfc_daily.unlink()


def main():
    parser = argparse.ArgumentParser(
        description='Descarga ERA5 por días completos, hace splithour y borra los originales.'
    )
    parser.add_argument('fecha_inicial', help='YYYY-MM-DD')
    parser.add_argument('fecha_final', help='YYYY-MM-DD')
    parser.add_argument('ruta', help='Directorio de descarga')
    args = parser.parse_args()

    start = datetime.strptime(args.fecha_inicial, '%Y-%m-%d').date()
    end = datetime.strptime(args.fecha_final, '%Y-%m-%d').date()

    if start > end:
        raise SystemExit('Error: la fecha inicial es posterior a la final')

    outdir = Path(args.ruta).expanduser().resolve()
    outdir.mkdir(parents=True, exist_ok=True)

    current = start
    while current <= end:
        process_day(current, outdir)
        current += timedelta(days=1)


if __name__ == '__main__':
    main()
