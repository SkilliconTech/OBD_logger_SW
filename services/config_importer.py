"""Turns a LoggerConfig read from a file into the ticks the screens use. No UI code."""
from dataclasses import dataclass, field

from models.pid_directory import get_entries

_ID_MODES = ("01", "02", "09")          # the modes that have a checkbox and a PID table


@dataclass
class ImportedSelection:
    modes: list = field(default_factory=list)      # ["01", "09"]
    pids: dict = field(default_factory=dict)       # {"01": {"0C": 250}, ...}
    frame: str = "00"                              # Mode 02 frame number
    skipped: list = field(default_factory=list)    # (request text, reason)


def selection_from_config(config):
    """Requests that the screens cannot show are listed in `skipped`."""
    result = ImportedSelection()
    known = {mode: {e.ident for e in get_entries(mode)} for mode in _ID_MODES}
    frame_chosen = False

    for item in config.requests:
        tokens = item.request.upper().split()
        mode = tokens[0] if tokens else ""
        if mode not in _ID_MODES:
            result.skipped.append((item.request, f"mode {mode} has no checkbox in this tool"))
            continue
        needed = 3 if mode == "02" else 2
        if len(tokens) < needed:
            result.skipped.append((item.request, "the request is incomplete"))
            continue
        ident = tokens[1]
        if ident not in known[mode]:
            result.skipped.append((item.request, f"{ident} is not in the Mode {mode} list"))
            continue
        if mode == "02":
            if not frame_chosen:
                result.frame = tokens[2]
                frame_chosen = True
            elif tokens[2] != result.frame:
                result.skipped.append(
                    (item.request, f"a different frame number (only {result.frame} is used)"))
                continue
        result.pids.setdefault(mode, {})[ident] = item.interval_ms
        if mode not in result.modes:
            result.modes.append(mode)

    result.modes.sort()
    return result