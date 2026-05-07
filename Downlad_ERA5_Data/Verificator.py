#!/home/jorge/miniconda3/bin/python
#This scripts checks if a given folder contains all necessary files to compute the advection. 
#@Author: J. Eiras-Barca 2026
#USAGE: 
#Mode 1: Yearly check : python Verificator.py ../ERA5/2022 2022
#Mode 2: Monthly check : python Verificator.py ../ERA5/2022 2022-01
#Mode 3: Daily check: python Verificator.py ../ERA5/2022 2022-01-03
#Check with verbose : python Verificator.py ../ERA5/2022/ 2022-01 --verbose
 
from pathlib import Path
from datetime import date, timedelta
import argparse
import calendar
import re
import sys

GREEN = "\033[92m"
RED = "\033[91m"
YELLOW = "\033[93m"
RESET = "\033[0m"

STEPS = ["00", "03", "06", "09", "12", "15", "18", "21"]

def parse_periodo(value: str):
    if re.fullmatch(r"\d{4}", value):
        year = int(value)
        start = date(year, 1, 1)
        end = date(year, 12, 31)
        return start, end, value

    if re.fullmatch(r"\d{4}-\d{2}", value):
        year = int(value[:4])
        month = int(value[5:7])
        if not (1 <= month <= 12):
            raise argparse.ArgumentTypeError("El mes debe estar entre 01 y 12")
        last_day = calendar.monthrange(year, month)[1]
        start = date(year, month, 1)
        end = date(year, month, last_day)
        return start, end, value

    if re.fullmatch(r"\d{4}-\d{2}-\d{2}", value):
        try:
            single_day = date.fromisoformat(value)
        except ValueError:
            raise argparse.ArgumentTypeError("Fecha no válida. Usa YYYY-MM-DD")
        return single_day, single_day, value

    raise argparse.ArgumentTypeError("Formato no válido. Usa YYYY, YYYY-MM o YYYY-MM-DD")

def daterange(start: date, end: date):
    current = start
    while current <= end:
        yield current
        current += timedelta(days=1)

def expected_files_for_day(day):
    ymd = day.strftime("%Y%m%d")
    ml_files = [f"ml_{ymd}_77_130_131_132_{hh}.nc" for hh in STEPS]
    b_files = [f"B{ymd}_sp_{hh}.nc" for hh in STEPS]
    return ml_files, b_files

def check_day(path: Path, day):
    ml_files, b_files = expected_files_for_day(day)

    missing_ml = [name for name in ml_files if not (path / name).is_file()]
    missing_b = [name for name in b_files if not (path / name).is_file()]

    complete = (len(missing_ml) == 0 and len(missing_b) == 0)
    return complete, missing_ml, missing_b

def main():
    parser = argparse.ArgumentParser(
        description="Verifica qué días están completos en una carpeta ERA5."
    )
    parser.add_argument("ruta", help="Ruta a la carpeta, por ejemplo ../ERA5/2022/")
    parser.add_argument("periodo", type=parse_periodo,
                        help="Periodo a comprobar: YYYY, YYYY-MM o YYYY-MM-DD")
    parser.add_argument("--verbose", action="store_true",
                        help="Muestra qué archivos faltan en los días incompletos")
    args = parser.parse_args()

    path = Path(args.ruta).expanduser().resolve()
    start, end, etiqueta = args.periodo

    if not path.is_dir():
        print(f"{RED}Error: la ruta no existe o no es un directorio: {path}{RESET}", file=sys.stderr)
        sys.exit(1)

    ok_count = 0
    bad_count = 0

    print(f"Comprobando periodo {etiqueta} en {path}\n")

    for day in daterange(start, end):
        complete, missing_ml, missing_b = check_day(path, day)
        day_str = day.strftime("%Y-%m-%d")

        if complete:
            ok_count += 1
            print(f"{GREEN}{day_str}: OK{RESET}")
        else:
            bad_count += 1
            print(f"{RED}{day_str}: INCOMPLETO{RESET}")
            if args.verbose:
                if missing_ml:
                    print(f"{YELLOW}  Faltan ml:{RESET}")
                    for name in missing_ml:
                        print(f"    {name}")
                if missing_b:
                    print(f"{YELLOW}  Faltan B:{RESET}")
                    for name in missing_b:
                        print(f"    {name}")

    print()
    print(f"{GREEN}Días completos: {ok_count}{RESET}")
    print(f"{RED}Días incompletos: {bad_count}{RESET}")

if __name__ == "__main__":
    main()
