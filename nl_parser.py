"""
Natural language parser for timer input.

Supports:
  25           → 25 minutes
  25m / 25min / 25mins / 25 minutes
  1h / 1hr / 1hour / 1 hour
  1h30m / 1 hour 30 mins / 1hr 30
  half hour / quarter hour
  90           → 90 minutes (bare numbers > 59 treated as minutes)
  10:30pm      → countdown to that time today (or tomorrow if past)
  add 10 mins  → returns a delta (positive int) to be added to remaining
"""

import re
from datetime import datetime, timedelta


_WORD_NUMBERS = {
    "half": 0.5, "quarter": 0.25,
    "one": 1, "two": 2, "three": 3, "four": 4, "five": 5,
    "six": 6, "seven": 7, "eight": 8, "nine": 9, "ten": 10,
    "fifteen": 15, "twenty": 20, "thirty": 30, "forty": 40,
    "forty-five": 45, "sixty": 60,
}


def parse(text: str) -> dict | None:
    """
    Returns:
        {"seconds": int}          — absolute duration
        {"add_seconds": int}      — delta to add to running timer
        None                      — unparseable
    """
    raw = text.strip().lower()
    if not raw:
        return None

    # --- "add X" prefix ---
    add_match = re.match(r'^add\s+(.*)', raw)
    if add_match:
        inner = parse(add_match.group(1))
        if inner and "seconds" in inner:
            return {"add_seconds": inner["seconds"]}
        return None

    # --- clock time: 10:30pm / 22:30 / 7pm / 7am ---
    clock = re.match(
        r'^(\d{1,2})(?::(\d{2}))?\s*(am|pm)?$', raw
    )
    if clock and clock.group(3):  # require am/pm when no colon+minutes
        h = int(clock.group(1))
        m = int(clock.group(2)) if clock.group(2) else 0
        meridiem = clock.group(3)
        if meridiem == "pm" and h != 12:
            h += 12
        elif meridiem == "am" and h == 12:
            h = 0
        now = datetime.now()
        target = now.replace(hour=h, minute=m, second=0, microsecond=0)
        if target <= now:
            target += timedelta(days=1)
        diff = int((target - now).total_seconds())
        return {"seconds": diff}

    # --- clock time without meridiem: 10:30 / 22:30 ---
    clock24 = re.match(r'^(\d{1,2}):(\d{2})$', raw)
    if clock24:
        h, m = int(clock24.group(1)), int(clock24.group(2))
        now = datetime.now()
        target = now.replace(hour=h, minute=m, second=0, microsecond=0)
        if target <= now:
            target += timedelta(days=1)
        diff = int((target - now).total_seconds())
        return {"seconds": diff}

    # --- word numbers at start: "half hour", "quarter hour" ---
    for word, factor in _WORD_NUMBERS.items():
        pattern = rf'^{re.escape(word)}\s*(hour|hr|hours|minute|min|mins|minutes)?$'
        m = re.match(pattern, raw)
        if m:
            unit = m.group(1) or "hour"
            if unit.startswith("h"):
                return {"seconds": int(factor * 3600)}
            else:
                return {"seconds": int(factor * 60)}

    # --- general h/m/s parser ---
    seconds = _parse_hms(raw)
    if seconds is not None:
        return {"seconds": seconds}

    return None


def _parse_hms(text: str) -> int | None:
    total = 0
    found = False

    # hours
    h = re.search(r'(\d+(?:\.\d+)?)\s*(?:hours?|hrs?|h)(?![a-zA-Z])', text)
    if h:
        total += float(h.group(1)) * 3600
        found = True

    # minutes
    m = re.search(r'(\d+(?:\.\d+)?)\s*(?:minutes?|mins?|m)(?![a-zA-Z])', text)
    if m:
        total += float(m.group(1)) * 60
        found = True

    # seconds
    s = re.search(r'(\d+(?:\.\d+)?)\s*(?:seconds?|secs?|s)(?![a-zA-Z])', text)
    if s:
        total += float(s.group(1))
        found = True

    if found:
        return int(total)

    # bare number: treat as seconds
    bare = re.match(r'^(\d+)$', text.strip())
    if bare:
        return int(bare.group(1))

    return None


if __name__ == "__main__":
    tests = [
        "25", "25m", "1h", "1h30m", "1 hour 30 mins",
        "half hour", "quarter hour", "add 10 mins",
        "10:30pm", "90", "45 seconds", "1.5h",
    ]
    for t in tests:
        print(f"{t!r:25} → {parse(t)}")
