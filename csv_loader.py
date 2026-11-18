"""Reading CSV files into flight records and error messages."""
import csv
import os

from validator import validate_row, to_record


def parse_files(paths: list[str], airports: set[str]) -> tuple[list[dict], list[str]]:
    """Process the CSV files in the order given.

    Return (records, errors); errors are formatted as
    "<file name>:<line number>: <ERROR_CODE> | <free text>".
    Also performs the DUPLICATE_FLIGHT check across all the files.
    """
    records: list[dict] = []
    errors: list[str] = []
    seen: set[tuple[str, str]] = set()

    for path in paths:
        name = os.path.basename(path)
        with open(path, encoding="utf-8-sig", newline="") as f:
            text = f.read()
        
        lines = text.split("\n")
        for number, line in enumerate(lines, start=1):
            if line.endswith("\r"):
                line = line[:-1]
            if number == 1:
                continue  # header
            stripped = line.strip()
            if not stripped or stripped.startswith("#"):
                continue
            try:
                fields = next(csv.reader([line]))
            except (csv.Error, StopIteration):
                fields = []
            code = validate_row(fields, airports)
            if code is None:
                record = to_record(fields)
                key = (record["flight_id"], record["departure_datetime"])
                if key in seen:
                    code = "DUPLICATE_FLIGHT"
                else:
                    seen.add(key)
                    records.append(record)
            if code is not None:
                errors.append(f"{name}:{number}: {code} | {line}")
    return records, errors