"""Writes config.json to the places the user chose, in the background. No UI code."""
from pathlib import Path
from models import config_rules as R
from dataclasses import dataclass, field

from services.config_file import export_config
from services.config_validator import validate


@dataclass
class SyncResult:
    saved: list = field(default_factory=list)     # full paths that were written
    failed: list = field(default_factory=list)    # (target, error text)
    issues: list = field(default_factory=list)    # problems found: nothing was written
    no_target: bool = False                       # valid, but nowhere to save yet


class ConfigSync:
    def __init__(self):
        self.folder = ""        # folder the user picked
        self.drive = ""         # logger drive, e.g. "E:\\"

    def targets(self):
        unique = []
        for target in (self.folder, self.drive):
            if target and target not in unique:
                unique.append(target)
        return unique

    def sync(self, config):
        """Validates, then writes config.json to every chosen target.
        An invalid configuration is never written."""
        result = SyncResult()
        issues = validate(config)
        if issues:
            result.issues = issues
            return result
        targets = self.targets()
        if not targets:
            result.no_target = True
            return result
        
        for target in targets:
            try:
                folder = target
                if target == self.drive:                       # logger card: use CONFIG
                    folder = Path(target) / R.CONFIG_FOLDER
                    if not folder.is_dir():
                        raise OSError(f'The "{R.CONFIG_FOLDER}" folder was not found on {target}.')
                result.saved.append(str(export_config(config, folder)))
            except OSError as error:
                result.failed.append((target, str(error)))


def describe_result(result):
    """One line for the status bar."""
    if result.issues:
        first = result.issues[0]
        more = f" (+{len(result.issues) - 1} more)" if len(result.issues) > 1 else ""
        return f"config.json not updated: {first.message} {first.fix}{more}"
    if result.no_target:
        return "config.json is ready. Choose a save folder or the logger drive to save it."
    parts = []
    if result.saved:
        parts.append("config.json saved to " + ", ".join(result.saved))
    if result.failed:
        parts.append("could not save to " + ", ".join(t for t, _ in result.failed))
    return "; ".join(parts)