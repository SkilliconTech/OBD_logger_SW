"""Checks a LoggerConfig against the logger's rules. No UI code.

validate(config) returns a list of ConfigIssue. An empty list means the
configuration is valid and may be exported."""
import re
from typing import NamedTuple

from models import config_rules as R
from services.config_serializer import to_json_text

_HEX = re.compile(r"^[0-9A-Fa-f]+$")
_BYTE = re.compile(r"^[0-9A-Fa-f]{2}$")


class ConfigIssue(NamedTuple):
    field: str      # which field is wrong, e.g. "requests[3].interval_ms"
    message: str    # what is wrong
    fix: str        # how to correct it


def _is_int(value):
    return isinstance(value, int) and not isinstance(value, bool)


def _check_number(issues, name, value, low, high, allow_zero=False):
    if not _is_int(value):
        issues.append(ConfigIssue(name, f"{name} must be a whole number.",
                                  f"Enter an integer from {low} to {high}."))
    elif not (low <= value <= high or (allow_zero and value == 0)):
        zero = " (or 0 for continuous run)" if allow_zero else ""
        issues.append(ConfigIssue(name, f"{name} is {value}, which is out of range.",
                                  f"Enter a value from {low} to {high}{zero}."))


def _check_ids(config, issues):
    bits = config.address_bits
    if bits not in R.ADDRESS_BITS:
        return                                    # can't judge the IDs without it
    parsed = {}
    for name in ("tx_id", "rx_id"):
        value = getattr(config, name)
        if not isinstance(value, str) or not _HEX.match(value):
            issues.append(ConfigIssue(
                name, f"{name} must be a hexadecimal string without 0x.",
                "Use only the digits 0-9 and letters A-F, for example 7DF."))
        elif int(value, 16) > R.MAX_ID[bits]:
            issues.append(ConfigIssue(
                name, f"{name} {value} is too large for {bits}-bit addressing.",
                f"Use a value up to {R.MAX_ID[bits]:X}, or change address_bits."))
        else:
            parsed[name] = int(value, 16)
    if len(parsed) < 2:
        return

    functional = R.FUNCTIONAL_IDS[bits]
    tx, rx = parsed["tx_id"], parsed["rx_id"]
    if rx == 0:                                   # functional request
        if tx != int(functional, 16):
            issues.append(ConfigIssue(
                "tx_id", f"A functional request must use tx_id {functional}.",
                f"Set tx_id to {functional}, or enter a nonzero rx_id for a physical request."))
    else:                                         # physical request
        if tx == int(functional, 16):
            issues.append(ConfigIssue(
                "tx_id", "For a physical request tx_id cannot be the functional ID.",
                "Use the ECU's own request ID, or set rx_id to 0 for a functional request."))
        if tx == rx:
            issues.append(ConfigIssue(
                "rx_id", "tx_id and rx_id must be different.",
                "Give the receive ID a different value from the transmit ID."))


def _check_request_text(label, text):
    """Returns a ConfigIssue for a bad request text, or None."""
    name = f"{label}.request"
    if not isinstance(text, str):
        return ConfigIssue(name, "The request must be text.", "Example: 01 0C")
    tokens = text.split()
    if not tokens or not all(_BYTE.match(t) for t in tokens):
        return ConfigIssue(name, f'"{text}" is not made of two-digit hex bytes.',
                           "Write bytes separated by spaces, for example 01 0C.")
    mode = tokens[0].upper()
    if mode == "04":
        return ConfigIssue(name, "Mode 04 is controlled by the logger's button.",
                           "Remove this request. Mode 04 cannot be in config.json.")
    if mode not in R.REQUEST_SHAPES:
        return ConfigIssue(name, f"Mode {mode} is not supported.",
                           "Use mode 01, 02, 06, 09, 03, 07 or 0A.")
    expected = R.REQUEST_SHAPES[mode]
    if len(tokens) - 1 != expected:
        return ConfigIssue(
            name, f"Mode {mode} needs {expected} byte(s) after it, not {len(tokens) - 1}.",
            f"Example: {R.REQUEST_EXAMPLES[mode]}")
    return None


def _check_requests(config, issues):
    requests = config.requests
    if not isinstance(requests, list) or not requests:
        issues.append(ConfigIssue("requests", "At least one request is required.",
                                  "Select at least one PID or mode."))
        return
    if len(requests) > R.MAX_REQUESTS:
        issues.append(ConfigIssue(
            "requests", f"There are {len(requests)} requests; the limit is {R.MAX_REQUESTS}.",
            f"Untick some items until {R.MAX_REQUESTS} or fewer remain."))

    seen = {}
    for i, item in enumerate(requests, 1):
        label = f"requests[{i}]"
        problem = _check_request_text(label, item.request)
        if problem:
            issues.append(problem)
        else:
            key = " ".join(item.request.upper().split())
            if key in seen:
                issues.append(ConfigIssue(
                    f"{label}.request", f'"{key}" is already request {seen[key]}.',
                    "Remove the duplicate; every request must be unique."))
            else:
                seen[key] = i
        _check_number(issues, f"{label}.interval_ms", item.interval_ms,
                      *R.INTERVAL_MS)


def validate(config):
    issues = []
    if not _is_int(config.version) or config.version != R.FORMAT_VERSION:
        issues.append(ConfigIssue("version", "version must be the integer 1.",
                                  "Set version to 1."))
    if config.bitrate not in R.BITRATES:
        issues.append(ConfigIssue(
            "bitrate", f"bitrate {config.bitrate} is not supported.",
            "Choose one of " + ", ".join(str(b) for b in R.BITRATES) + "."))
    if config.address_bits not in R.ADDRESS_BITS:
        issues.append(ConfigIssue("address_bits", "address_bits must be 11 or 29.",
                                  "Choose 11-bit or 29-bit addressing."))
    _check_ids(config, issues)
    _check_number(issues, "startup_delay_ms", config.startup_delay_ms,
                  *R.STARTUP_DELAY_MS)
    _check_number(issues, "run_duration_ms", config.run_duration_ms,
                  *R.RUN_DURATION_MS, allow_zero=True)
    _check_number(issues, "response_timeout_ms", config.response_timeout_ms,
                  *R.RESPONSE_TIMEOUT_MS)
    _check_requests(config, issues)

    try:                                          # the file must also fit in 8192 bytes
        size = len(to_json_text(config).encode("utf-8"))
        if size > R.MAX_FILE_BYTES:
            issues.append(ConfigIssue(
                "file", f"The file would be {size} bytes; the limit is {R.MAX_FILE_BYTES}.",
                "Remove some requests."))
    except (AttributeError, TypeError):
        pass
    return issues