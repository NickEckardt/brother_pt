"""
   Copyright 2022 Thomas Reidemeister

   Licensed under the Apache License, Version 2.0 (the "License");
   you may not use this file except in compliance with the License.
   You may obtain a copy of the License at

       http://www.apache.org/licenses/LICENSE-2.0

   Unless required by applicable law or agreed to in writing, software
   distributed under the License is distributed on an "AS IS" BASIS,
   WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
   See the License for the specific language governing permissions and
   limitations under the License.
"""
import re
import socket
import subprocess


def find_rfcomm_channel(address: str):
    """Best-effort SPP channel lookup via sdptool. Returns None if unavailable."""
    try:
        output = subprocess.run(
            ["sdptool", "browse", address],
            capture_output=True, text=True, timeout=10, check=True,
        ).stdout
    except (FileNotFoundError, subprocess.CalledProcessError, subprocess.TimeoutExpired):
        return None

    for service in output.split("Service Name:"):
        if "Serial Port" not in service:
            continue
        match = re.search(r"Channel:\s*(\d+)", service)
        if match:
            return int(match.group(1))
    return None


class BluetoothTransport:
    def __init__(self, address: str, channel: int = 1, timeout: float = 15):
        self._sock = socket.socket(socket.AF_BLUETOOTH, socket.SOCK_STREAM, socket.BTPROTO_RFCOMM)
        self._sock.settimeout(timeout)
        self._sock.connect((address, channel))

    def write(self, data: bytes) -> int:
        self._sock.sendall(data)
        return len(data)

    def read(self, length: int = 0x80) -> bytes:
        try:
            return self._sock.recv(length)
        except socket.timeout:
            raise RuntimeError("IO timeout while reading from printer")

    def close(self) -> None:
        self._sock.close()
