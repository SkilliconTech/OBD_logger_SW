"""Turns a LoggerConfig into config.json text and back. No validation here."""
import json

from models.logger_config import LoggerConfig, Request

KEYS = ("version", "bitrate", "address_bits", "tx_id", "rx_id",
        "startup_delay_ms", "run_duration_ms", "response_timeout_ms", "requests")
REQUEST_KEYS = ("request", "interval_ms")


class ConfigFormatError(ValueError):
    """The text is not a config.json the logger could read."""


def to_dict(config):
    data = {key: getattr(config, key) for key in KEYS if key != "requests"}
    data["requests"] = [{"request": r.request, "interval_ms": r.interval_ms}
                        for r in config.requests]
    return data


def to_json_text(config):
    return json.dumps(to_dict(config), indent=2, ensure_ascii=False) + "\n"


def from_dict(data):
    if not isinstance(data, dict):
        raise ConfigFormatError("The file must contain one JSON object.")
    unknown = sorted(set(data) - set(KEYS))
    if unknown:
        raise ConfigFormatError(
            "Unknown key(s): " + ", ".join(unknown) + ". The firmware rejects them.")
    missing = [k for k in KEYS if k not in data]
    if missing:
        raise ConfigFormatError("Missing key(s): " + ", ".join(missing) + ".")
    if not isinstance(data["requests"], list):
        raise ConfigFormatError('"requests" must be a list.')

    requests = []
    for i, item in enumerate(data["requests"], 1):
        if not isinstance(item, dict) or set(item) != set(REQUEST_KEYS):
            raise ConfigFormatError(
                f'requests[{i}] must contain only "request" and "interval_ms".')
        requests.append(Request(item["request"], item["interval_ms"]))

    values = {k: data[k] for k in KEYS if k != "requests"}
    return LoggerConfig(**values, requests=requests)


def from_json_text(text):
    try:
        data = json.loads(text)
    except json.JSONDecodeError as error:
        raise ConfigFormatError(f"The file is not valid JSON: {error}") from error
    return from_dict(data)