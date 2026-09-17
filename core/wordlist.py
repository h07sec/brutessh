from pathlib import Path

def load_wordlist(filename):
    path = Path(filename).expanduser()
    if not path.is_file():
        raise FileNotFoundError(str(path))
    values, seen = [], set()
    with path.open("r", encoding="utf-8", errors="ignore") as fh:
        for line in fh:
            value = line.strip()
            if value and not value.startswith("#") and value not in seen:
                values.append(value)
                seen.add(value)
    return values
