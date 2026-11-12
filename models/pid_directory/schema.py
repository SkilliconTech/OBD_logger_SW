from typing import NamedTuple


class Entry(NamedTuple):
    """One row of a mode's table (a PID, test ID or InfoType)."""
    ident: str          # "0C" for a single ID, or a range / label such as "$01-$0A"
    name: str
    description: str


class ModeInfo(NamedTuple):
    """Heading information for one mode page."""
    code: str           # "01"
    name: str           # "Live powertrain data"
    summary: str        # "Reads current emissions-related measurements and status."
    id_label: str       # column title: "PID", "TID", "OBDMID / TID", "InfoType", ""
    selectable: bool    # True -> rows get a checkbox
    note: str = ""      # extra text shown under the table