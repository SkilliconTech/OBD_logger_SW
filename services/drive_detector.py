"""Finds removable drives (SD card readers, USB sticks) on Windows. No UI code."""
import ctypes
import string
import sys

_DRIVE_REMOVABLE = 2


def _volume_label(root):
    buffer = ctypes.create_unicode_buffer(261)
    ok = ctypes.windll.kernel32.GetVolumeInformationW(
        root, buffer, 261, None, None, None, None, 0)
    return buffer.value if ok else ""


def list_removable_drives():
    """Returns [(root, text_to_show)], e.g. [("E:\\\\", "E:\\\\  LOGGER")].
    Returns an empty list on systems other than Windows."""
    if sys.platform != "win32":
        return []
    drives = []
    bitmask = ctypes.windll.kernel32.GetLogicalDrives()
    for index, letter in enumerate(string.ascii_uppercase):
        if not bitmask & (1 << index):
            continue
        root = f"{letter}:\\"
        if ctypes.windll.kernel32.GetDriveTypeW(root) == _DRIVE_REMOVABLE:
            label = _volume_label(root)
            drives.append((root, f"{root}  {label}".strip()))
    return drives