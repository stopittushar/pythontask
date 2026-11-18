"""Flight Schedule Parser and Query Tool - command-line entry point.

Run from the project folder, for example:
    python flight_parser.py -i data/db.csv -a data/airports.txt
"""
import argparse
import json
import logging
import os
import sys
from datetime import datetime

from csv_loader import parse_files
from query import run_queries
from validator import load_airports

STUDENT_ID = "251ADB110"   
FIRST_NAME = "Tushar"   
LAST_NAME = "SohanLal"     


class RuntimeProblem(Exception):
    """An expected runtime problem; reported as 'Error: ...' with exit code 1."""


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="flight_parser.py",
        description="Validate flight CSV files, store valid flights as JSON "
                    "and answer queries.")
    parser.add_argument("-i", metavar="FILE", help="parse a single CSV file")
    parser.add_argument("-d", metavar="FOLDER", help="parse every .csv file in a folder")
    parser.add_argument("-j", metavar="FILE", help="load an existing JSON database")
    parser.add_argument("-a", metavar="FILE", help="airport list file (required with -i/-d)")
    parser.add_argument("-o", metavar="FILE", help="output JSON database (default: db.json)")
    parser.add_argument("-q", metavar="FILE", help="JSON file with queries")
    parser.add_argument("-r", metavar="FOLDER", help="folder for the response file (default: .)")
    return parser


def read_json(path: str, what: str):
    try:
        with open(path, encoding="utf-8-sig") as f:
            return json.load(f)
    except OSError as exc:
        raise RuntimeProblem(f"cannot read {what} '{path}': {exc.strerror or exc}")
    except (ValueError, UnicodeDecodeError) as exc:
        raise RuntimeProblem(f"{what} '{path}' is not valid JSON: {exc}")


def write_json(path: str, data) -> None:
    try:
        with open(path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
            f.write("\n")
    except OSError as exc:
        raise RuntimeProblem(f"cannot write '{path}': {exc.strerror or exc}")


def write_error_log(log_path: str, errors: list[str]) -> None:
    logger = logging.getLogger("flight_parser")
    logger.setLevel(logging.INFO)
    handler = None
    try:
        try:
            handler = logging.FileHandler(log_path, mode="w", encoding="utf-8")
        except OSError as exc:
            raise RuntimeProblem(f"cannot write '{log_path}': {exc.strerror or exc}")
        handler.setFormatter(logging.Formatter(
            "%(asctime)s %(levelname)s %(message)s", datefmt="%Y-%m-%d %H:%M:%S"))
        logger.addHandler(handler)
        for message in errors:
            logger.warning(message)
    finally:
        if handler is not None:
            logger.removeHandler(handler)
            handler.close()


def collect_csv_paths(folder: str) -> list[str]:
    try:
        names = os.listdir(folder)
    except OSError as exc:
        raise RuntimeProblem(f"cannot read folder '{folder}': {exc.strerror or exc}")
    paths = [os.path.join(folder, n) for n in sorted(names)
             if n.endswith(".csv") and os.path.isfile(os.path.join(folder, n))]
    if not paths:
        raise RuntimeProblem(f"no .csv files found in '{folder}'")
    return paths


def load_database(path: str) -> list[dict]:
    db = read_json(path, "database")
    if not isinstance(db, list) or not all(isinstance(r, dict) for r in db):
        raise RuntimeProblem(f"database '{path}' must be a JSON array of objects")
    return db


def run(args, parser) -> None:
    sources = [s for s in (args.i, args.d, args.j) if s is not None]
    if len(sources) != 1:
        parser.error("exactly one of -i, -d or -j is required")
    if args.j is None and args.a is None:
        parser.error("-a is required with -i and -d")
    if args.j is not None and args.o is not None:
        parser.error("-o cannot be used with -j")

    if args.j is not None:
        db = load_database(args.j)
    else:
        try:
            airports = load_airports(args.a)
        except OSError as exc:
      
            raise RuntimeProblem(f"cannot read airport file '{args.a}': {exc.strerror or exc}")
      
        except UnicodeDecodeError as exc:
      
            raise RuntimeProblem(f"airport file '{args.a}' is not valid UTF-8: {exc}")
      
        paths = [args.i] if args.i is not None else collect_csv_paths(args.d)
        try:
            db, errors = parse_files(paths, airports)
        except OSError as exc:
            raise RuntimeProblem(f"cannot read CSV file: {exc.filename or ''}: {exc.strerror or exc}")
        except UnicodeDecodeError as exc:
            raise RuntimeProblem(f"CSV file is not valid UTF-8: {exc}")

      
        db_path = args.o if args.o is not None else "db.json"
      
        log_path = os.path.join(os.path.dirname(db_path), "errors.log")
      
        write_json(db_path, db)
      
        write_error_log(log_path, errors)
      
        print(f"{len(db)} valid flights, {len(errors)} invalid rows; database: {db_path}")

    if args.q is not None:
        queries = read_json(args.q, "query file")
        if not isinstance(queries, (dict, list)):
            raise RuntimeProblem(f"query file '{args.q}' must contain an object or an array")
      
        response = run_queries(db, queries)
      
        stamp = datetime.now().strftime("%Y%m%d_%H%M")
      
        name = f"response_{STUDENT_ID}_{FIRST_NAME}_{LAST_NAME}_{stamp}.json"
      
        folder = args.r if args.r is not None else "."
      
        out_path = os.path.join(folder, name)
      
        write_json(out_path, response)
      
        print(f"{len(response)} queries answered; response: {out_path}")


def main(argv: list[str] | None = None) -> int:
    """Runprogram and return exit code"""
    parser = build_parser()
    try:
        args = parser.parse_args(argv)
        run(args, parser)
    except SystemExit as exc:  # argparse usage errors and -h
        return exc.code if isinstance(exc.code, int) else 2
    except RuntimeProblem as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 1
    except OSError as exc:
        print(f"Error: {exc.strerror or exc}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())