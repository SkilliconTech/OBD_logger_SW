"""Finds the logger when it is plugged in over USB as an MTP portable device and copies
config.json to the CONFIG folder of its SD card, then reads the file back to check it.
Windows only. No UI code.

An MTP device has no drive letter, so normal file writes cannot reach it. This module uses
the Windows Shell (the same engine Explorer uses) through PowerShell, so it needs no extra
Python package.

Device:  This PC > OBD_<factory number> > SD card > CONFIG > config.json
"""
import hashlib
import os
import subprocess
import sys
import tempfile
from dataclasses import dataclass, field

from models import config_rules as R

MTP_PREFIX = "mtp:"                 # marks an MTP choice in the logger dropdown
DEVICE_PREFIX = "OBD_"              # the logger shows up as OBD_<factory number>
STORAGE_NAME = "SD card"            # the storage inside the device
CONFIG_NAME = "config.json"
SCAN_TIMEOUT_S = 20
TRANSFER_TIMEOUT_S = 60
SUCCESS_TEXT = "Transfer complete\u2014restart the logger to apply."


@dataclass
class MtpDevice:
    name: str                                        # e.g. "OBD_1757338"
    storages: list = field(default_factory=list)     # storage names the device shows now

    @property
    def storage_ready(self):
        """True when the SD card can be written to. It is missing while the logger is
        logging, and appears after logging stops and buffered data is saved."""
        return any(s.lower() == STORAGE_NAME.lower() for s in self.storages)


@dataclass
class TransferResult:
    ok: bool
    message: str


# ---------------------------------------------------------------- PowerShell scripts
# Plain ASCII on purpose. Each script prints one status line: CODE<TAB>text.

_LIST_SCRIPT = r"""
[Console]::OutputEncoding = [System.Text.Encoding]::UTF8
$ErrorActionPreference = 'Stop'
$shell = New-Object -ComObject Shell.Application
foreach ($item in $shell.Namespace(17).Items()) {
    if ($item.Name -like 'OBD_*') {
        $names = @()
        try {
            $folder = $item.GetFolder
            if ($folder) { foreach ($s in $folder.Items()) { $names += $s.Name } }
        } catch { }
        Write-Output ("DEVICE`t" + $item.Name + "`t" + ($names -join ';'))
    }
}
"""

_SEND_SCRIPT = r"""
param([string]$Device, [string]$Storage, [string]$Folder, [string]$Source, [string]$ExpectedHash, [int]$TimeoutSec)
[Console]::OutputEncoding = [System.Text.Encoding]::UTF8
$ErrorActionPreference = 'Stop'
$shell = New-Object -ComObject Shell.Application

function Finish([string]$code, [string]$text) {
    Write-Output ($code + "`t" + $text)
    exit 0
}
function Find-Child($items, [string]$name) {
    foreach ($i in $items) { if ($i.Name -eq $name) { return $i } }
    return $null
}
function Find-Storage() {
    $dev = Find-Child ($shell.Namespace(17).Items()) $Device
    if (-not $dev) { Finish 'NODEVICE' $Device }
    $folder = $null
    try { $folder = $dev.GetFolder } catch { }
    if (-not $folder) { Finish 'NOSTORAGE' $Device }
    $store = Find-Child ($folder.Items()) $Storage
    if (-not $store) { Finish 'NOSTORAGE' $Device }
    return $store
}
function Find-Target() {                      # the CONFIG folder inside the SD card
    $store = Find-Storage
    $dir = Find-Child ($store.GetFolder.Items()) $Folder
    if ((-not $dir) -or (-not $dir.IsFolder)) { Finish 'NOFOLDER' $Folder }
    return $dir
}

# 1. copy into SD card / CONFIG (4 = no progress box, 16 = yes to all)
$target = Find-Target
$target.GetFolder.CopyHere($Source, 20)

# 2. wait until the file on the device is byte-for-byte the file we sent
$deadline = (Get-Date).AddSeconds($TimeoutSec)
$reason = 'The file did not appear on the logger.'
$verified = $false
while ((Get-Date) -lt $deadline) {
    Start-Sleep -Milliseconds 1000
    $target = Find-Target                      # also notices an unplugged device
    $file = $null
    foreach ($f in $target.GetFolder.Items()) {
        if ($f.IsFolder) { continue }
        # Explorer may hide the .json extension, so accept both names
        if (($f.Name -eq 'config.json') -or ($f.Name -eq 'config')) { $file = $f; break }
    }
    if (-not $file) { continue }
    $check = Join-Path ([System.IO.Path]::GetTempPath()) ('obdcheck_' + [guid]::NewGuid().ToString('N'))
    New-Item -ItemType Directory -Path $check | Out-Null
    try {
        $shell.Namespace($check).CopyHere($file, 20)
        $local = $null
        for ($n = 0; $n -lt 10; $n++) {
            Start-Sleep -Milliseconds 500
            $found = Get-ChildItem -LiteralPath $check -File -ErrorAction SilentlyContinue | Select-Object -First 1
            if ($found) { $local = $found.FullName; break }
        }
        if ($local) {
            Start-Sleep -Milliseconds 300
            $actual = ''
            try { $actual = (Get-FileHash -LiteralPath $local -Algorithm SHA256).Hash } catch { }
            if ($actual -eq $ExpectedHash) { $verified = $true }
            else { $reason = 'The file on the logger is different from the file that was sent.' }
        } else { $reason = 'The file on the logger could not be read back.' }
    } finally {
        Remove-Item -LiteralPath $check -Recurse -Force -ErrorAction SilentlyContinue
    }
    if ($verified) { break }
}
if ($verified) { Finish 'OK' 'verified' }
Finish 'TIMEOUT' $reason
"""


def _run_powershell(script, args=(), timeout=30):
    """Runs a PowerShell script from a temporary file. Returns (exit code, stdout, stderr)."""
    with tempfile.TemporaryDirectory(prefix="obdmtp_") as folder:
        path = os.path.join(folder, "task.ps1")
        with open(path, "w", encoding="utf-8") as handle:
            handle.write(script)
        command = ["powershell", "-NoProfile", "-NonInteractive",
                   "-ExecutionPolicy", "Bypass", "-File", path, *[str(a) for a in args]]
        done = subprocess.run(
            command, capture_output=True, text=True, encoding="utf-8", errors="replace",
            timeout=timeout, creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0))
        return done.returncode, done.stdout, done.stderr


# ---------------------------------------------------------------- finding the logger

def _parse_devices(output):
    devices = []
    for line in output.splitlines():
        parts = line.rstrip("\r").split("\t")
        if len(parts) < 2 or parts[0] != "DEVICE":
            continue
        if not parts[1].upper().startswith(DEVICE_PREFIX):
            continue
        storages = [s for s in (parts[2].split(";") if len(parts) > 2 else []) if s]
        devices.append(MtpDevice(parts[1], storages))
    return sorted(devices, key=lambda d: d.name)


def list_mtp_devices():
    """Loggers plugged in over USB, with the storage each one shows right now.
    Returns [] on systems other than Windows or when nothing is found."""
    if sys.platform != "win32":
        return []
    try:
        code, output, _ = _run_powershell(_LIST_SCRIPT, timeout=SCAN_TIMEOUT_S)
    except (OSError, subprocess.TimeoutExpired):
        return []
    return _parse_devices(output) if code == 0 else []


# ---------------------------------------------------------------- sending config.json

def _result_from_output(device, code, output, error):
    reply = ""
    for line in output.splitlines():
        if "\t" in line:
            reply = line.rstrip("\r")                  # the last status line wins
    status, _, detail = reply.partition("\t")
    if status == "OK":
        return TransferResult(True, SUCCESS_TEXT)
    if status == "NODEVICE":
        return TransferResult(False, f"{device} is not connected. "
                                     "Reconnect the USB cable and try again.")
    if status == "NOSTORAGE":
        return TransferResult(False, f"The {STORAGE_NAME} on {device} is not available. "
                                     "The logger shows it only after logging stops and "
                                     "buffered data is saved.")
    if status == "NOFOLDER":
        return TransferResult(False, f'The "{R.CONFIG_FOLDER}" folder was not found on the '
                                     f"{STORAGE_NAME} of {device}. Check that the card has a "
                                     f'"{R.CONFIG_FOLDER}" folder, then try again.')
    if status == "TIMEOUT":
        return TransferResult(False, f"config.json could not be confirmed on the logger. "
                                     f"{detail} If Windows asked to replace the existing "
                                     "file, choose Copy and Replace, then send again.")
    problem = error.strip() or output.strip() or "no details"
    return TransferResult(False, f"The transfer failed (exit code {code}): {problem}")


def send_config(device_name, text, timeout_s=TRANSFER_TIMEOUT_S):
    """Copies `text` to <device>/SD card/CONFIG/config.json, replacing any file there, and
    reads it back to check the SHA-256. Blocks until done: call it from a background thread."""
    if sys.platform != "win32":
        return TransferResult(False, "Sending to the logger over USB works on Windows only.")
    data = text.encode("utf-8")
    if len(data) > R.MAX_FILE_BYTES:
        return TransferResult(False, f"config.json is {len(data)} bytes. The logger "
                                     f"accepts at most {R.MAX_FILE_BYTES} bytes.")
    digest = hashlib.sha256(data).hexdigest().upper()
    with tempfile.TemporaryDirectory(prefix="obdsend_") as folder:
        source = os.path.join(folder, CONFIG_NAME)
        with open(source, "wb") as handle:
            handle.write(data)
        try:
            code, output, error = _run_powershell(
                _SEND_SCRIPT,
                [device_name, STORAGE_NAME, R.CONFIG_FOLDER, source, digest, timeout_s],
                timeout=timeout_s + 30)
        except subprocess.TimeoutExpired:
            return TransferResult(False, "The transfer took too long and was stopped. "
                                         "Check the USB connection and try again.")
        except OSError as problem:
            return TransferResult(False, f"Could not start PowerShell: {problem}")
    return _result_from_output(device_name, code, output, error)