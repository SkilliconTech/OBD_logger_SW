"""OBD mode / PID directory (data only, no UI code).

    get_mode_info("01") -> ModeInfo
    get_entries("01")   -> tuple of Entry (empty for modes without IDs)
"""
from models.pid_directory.schema import Entry, ModeInfo
from models.pid_directory.mode_info import MODE_INFO
from models.pid_directory.data_pids import DATA_PIDS
from models.pid_directory.identifiers import MODE_05, MODE_06, MODE_08, MODE_09

_ENTRIES = {
    "01": tuple(e for e in DATA_PIDS if e.ident != "02"),   # $02 is Mode $02 only
    "02": DATA_PIDS,
    "05": MODE_05,
    "06": MODE_06,
    "08": MODE_08,
    "09": MODE_09,
}


def get_mode_info(code: str) -> ModeInfo:
    return MODE_INFO[code]


def get_entries(code: str):
    return _ENTRIES.get(code, ())