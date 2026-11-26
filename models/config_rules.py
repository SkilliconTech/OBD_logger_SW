"""Limits of the logger's config.json format (from config-generator.md).
Pure data, no UI code. If the firmware rules change, edit only this file."""

FORMAT_VERSION = 1
BITRATES = (125000, 250000, 500000, 1000000)
ADDRESS_BITS = (11, 29)

FUNCTIONAL_IDS = {11: "7DF", 29: "18DB33F1"}      # broadcast request IDs
MAX_ID = {11: 0x7FF, 29: 0x1FFFFFFF}              # highest valid CAN ID

STARTUP_DELAY_MS = (0, 600000)
RUN_DURATION_MS = (1000, 86400000)                # 0 also allowed = run continuously
RESPONSE_TIMEOUT_MS = (10, 10000)
INTERVAL_MS = (10, 3600000)

MAX_REQUESTS = 1000
MAX_FILE_BYTES = 10000000
CONFIG_FOLDER = "CONFIG"      # folder on the SD card that holds config.json

# service -> how many hex bytes follow it in a request
REQUEST_SHAPES = {"01": 1, "02": 2, "06": 1, "09": 1, "03": 0, "07": 0, "0A": 0}
REQUEST_EXAMPLES = {
    "01": "01 0C", "02": "02 0C 00", "06": "06 01", "09": "09 02",
    "03": "03", "07": "07", "0A": "0A",
}

TRANSFER_GUIDANCE = (
    "Copy config.json to the root of the logger's SD card (not inside a folder). "
    "Finish the transfer before restarting the logger so it can load the new file."
)