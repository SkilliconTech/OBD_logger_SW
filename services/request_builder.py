"""Builds the request text that goes into config.json."""


def build_request(mode, ident=None, frame=None):
    """build_request("01", "0C") -> "01 0C"
       build_request("02", "0C", "00") -> "02 0C 00"
       build_request("03") -> "03"
    """
    parts = [mode, ident, frame]
    return " ".join(p.strip().upper() for p in parts if p)