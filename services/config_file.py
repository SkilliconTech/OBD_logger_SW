"""Reads and writes config.json files. Refuses to export an invalid config."""
from pathlib import Path

from models.logger_config import LoggerConfig
from services.config_serializer import from_json_text, to_json_text
from services.config_validator import validate

CONFIG_FILE_NAME = "config.json"


class InvalidConfigError(ValueError):
    def __init__(self, issues):
        super().__init__(f"{len(issues)} problem(s) in the configuration.")
        self.issues = issues


def save_config_file(config: LoggerConfig, path) -> Path:
    """Writes the config to exactly this file. Raises InvalidConfigError while errors remain."""
    issues = validate(config)
    if issues:
        raise InvalidConfigError(issues)
    target = Path(path)
    with open(target, "w", encoding="utf-8", newline="\n") as handle:
        handle.write(to_json_text(config))
    return target

def export_config(config: LoggerConfig, folder) -> Path:
    """Writes folder/config.json."""
    return save_config_file(config, Path(folder) / CONFIG_FILE_NAME)

def import_config(path) -> LoggerConfig:
    """Reads a config.json. Raises ConfigFormatError if it can't be read."""
    with open(path, "r", encoding="utf-8-sig") as handle:
        return from_json_text(handle.read())