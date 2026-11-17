"""Builds a LoggerConfig from what the user ticked on the screens. No UI code."""
from dataclasses import replace

from models.logger_config import LoggerConfig, Request
from services.request_builder import build_request

DEFAULT_INTERVAL_MS = 1000          # until the screen lets the user type one
DEFAULT_FRAME = "00"                # Mode 02 needs a frame number
_ID_MODES = ("01", "02", "06", "09")        # modes that need an ID after them
_SINGLE_MODES = ("03", "07", "0A")          # modes that are just the mode byte


def build_config(selected_modes, selected_pids, base=None,frame=DEFAULT_FRAME):
    """selected_modes: ["01", "09"]   selected_pids: {"01": ["0C", "0D"], ...}
    Only ticked modes are used. `base` carries the settings (bitrate, IDs, ...)."""
    config = replace(base) if base is not None else LoggerConfig()
    requests = []
    for mode in _ID_MODES:
        if mode not in selected_modes:
            continue
        chosen = selected_pids.get(mode, {})
        if not isinstance(chosen, dict):              # a plain list of IDs
            chosen = {ident: DEFAULT_INTERVAL_MS for ident in chosen}
        for ident, interval in chosen.items():
            frame_part = frame if mode == "02" else None
            requests.append(Request(build_request(mode, ident, frame_part), interval))
    for mode in _SINGLE_MODES:
        if mode in selected_modes:
            requests.append(Request(build_request(mode), DEFAULT_INTERVAL_MS))
    config.requests = requests
    return config