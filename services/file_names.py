"""Turns what the user types into a safe config file name. Pure Python, no UI code."""
import re

DEFAULT_NAME = "config"
EXTENSION = ".json"
MAX_LENGTH = 60

_BAD_CHARS = re.compile(r'[\\/:*?"<>|\x00-\x1f]')
_RESERVED = {"CON", "PRN", "AUX", "NUL",
             *(f"COM{i}" for i in range(1, 10)), *(f"LPT{i}" for i in range(1, 10))}


def clean_file_name(text, taken=(), default=DEFAULT_NAME):
    """'  My test?.JSON ' -> 'My test.json'. Nothing usable -> 'new_config.json'.
    A name that is already in `taken` gets ' 2', ' 3' ... so two rows never share a name."""
    name = _BAD_CHARS.sub("", text or "").strip()
    while name.lower().endswith(EXTENSION):          # the user may or may not type .json
        name = name[:-len(EXTENSION)].rstrip()
    name = name.strip(" .")[:MAX_LENGTH].rstrip(" .") or default
    if name.upper() in _RESERVED:                    # Windows does not allow these names
        name += "_"
    used = {t.lower() for t in taken}
    candidate, number = name, 1
    while candidate.lower() + EXTENSION in used:
        number += 1
        candidate = f"{name} {number}"
    return candidate + EXTENSION