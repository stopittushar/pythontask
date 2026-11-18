"""Row validation: airport list loading, single-row checks, record building."""
import math
import re
from datetime import datetime

FLIGHT_ID_RE = re.compile(r"[A-Za-z0-9]{2,8}")
AIRPORT_RE = re.compile(r"[A-Z]{3}")
DATETIME_RE = re.compile(r"[0-9]{4}-[0-9]{2}-[0-9]{2} [0-9]{2}:[0-9]{2}")
DATETIME_FORMAT = "%Y-%m-%d %H:%M"


def parse_datetime(text: str) -> datetime | None:
    """Parse exactly 'YYYY-MM-DD HH:MM' (zero-padded, ASCII digits).

    Return none if text is not informat or is not real date,time.
    """
    if not isinstance(text, str) or not DATETIME_RE.fullmatch(text):
        return None
    try:
        return datetime.strptime(text, DATETIME_FORMAT)
    except ValueError:
        return None


def load_airports(path: str) -> set[str]:
    """Read airport list file and return set of codes."""
    codes = set()
    with open(path, encoding="utf-8-sig") as f:
        for line in f:
            code = line.strip()
            if not code or code.startswith("#"):
                continue
            codes.add(code)
    return codes


def validate_row(fields: list[str], airports: set[str]) -> str | None:
    """Return None if validotherwise the code ofFIRST failing check."""
    
    if len(fields) != 6:
        return "WRONG_FIELD_COUNT"
    flight_id, origin, destination, dep, arr, price = (f.strip() for f in fields)


    if not all((flight_id, origin, destination, dep, arr, price)):
        return "MISSING_FIELD"

   
    if not FLIGHT_ID_RE.fullmatch(flight_id):
        return "INVALID_FLIGHT_ID"

   
    if not AIRPORT_RE.fullmatch(origin) or origin not in airports:
        return "INVALID_ORIGIN"
    if not AIRPORT_RE.fullmatch(destination) or destination not in airports:
        return "INVALID_DESTINATION"

   
    if origin == destination:
        return "SAME_ORIGIN_DESTINATION"

    
    dep_dt = parse_datetime(dep)
    if dep_dt is None:
        return "INVALID_DEPARTURE"
    arr_dt = parse_datetime(arr)
    if arr_dt is None:
        return "INVALID_ARRIVAL"

    
    if arr_dt <= dep_dt:
        return "ARRIVAL_NOT_AFTER_DEPARTURE"

    
    try:
        value = float(price)
    except ValueError:
        return "INVALID_PRICE"
    if not math.isfinite(value):
        return "INVALID_PRICE"
    if value <= 0:
        return "NON_POSITIVE_PRICE"

    return None


def to_record(fields: list[str]) -> dict:
    """Turn a valid row into a flight record dictionary."""
    flight_id, origin, destination, dep, arr, price = (f.strip() for f in fields)
    return {
        "flight_id": flight_id,
        "origin": origin,
        "destination": destination,
        "departure_datetime": dep,
        "arrival_datetime": arr,
        "price": float(price),
    }