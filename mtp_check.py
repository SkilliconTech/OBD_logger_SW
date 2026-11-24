"""Run this on Windows with the logger plugged in over USB, from the project folder:

    python mtp_check.py                      list the loggers and whether the SD card is available
    python mtp_check.py --send OBD_1757338   send a small TEST config.json twice (checks replacing)

--send OVERWRITES config.json on the logger. Stop logging first so the SD card is available.
"""
import sys

from models.logger_config import LoggerConfig, Request
from services.config_serializer import to_json_text
from services.config_validator import validate
from services import mtp_device


def main(argv):
    if "--send" in argv:
        index = argv.index("--send")
        if index + 1 >= len(argv):
            print("Give the device name, for example: python mtp_check.py --send OBD_1757338")
            return 2
        name = argv[index + 1]
        config = LoggerConfig(requests=[Request("01 0C", 1000)])
        problems = validate(config)
        if problems:
            print("The test configuration is invalid:", problems[0].message)
            return 2
        text = to_json_text(config)
        for attempt in (1, 2):
            print(f"Send {attempt} of 2 (the second one replaces the first) ...")
            result = mtp_device.send_config(name, text)
            print("  ", "OK  " if result.ok else "FAIL", result.message)
            if not result.ok:
                return 1
        return 0

    devices = mtp_device.list_mtp_devices()
    if not devices:
        print("No OBD_ device found. Plug the logger in over USB (and stop logging).")
        return 1
    for device in devices:
        state = "SD card available" if device.storage_ready else "SD card NOT available"
        print(f"{device.name}: {state}   storages seen: {device.storages or 'none'}")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))