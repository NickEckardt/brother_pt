#!/usr/bin/env python3
"""Query a Brother PT printer's status over Bluetooth RFCOMM.

Requires the printer to already be paired/bonded (e.g. via `bluetoothctl`).

Usage:
    python3 bluetooth_status.py <bdaddr> [-c CHANNEL]

If -c/--channel is omitted, the RFCOMM channel is looked up automatically
via `sdptool browse <bdaddr>`. See examples/README.md if that lookup fails.
"""
import argparse
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from brother_pt.printer import BrotherPt
from brother_pt.bluetooth_transport import find_rfcomm_channel


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("address", help="Bluetooth device address, e.g. 94:DD:F8:A1:9E:98")
    parser.add_argument("-c", "--channel", type=int, default=None,
                         help="RFCOMM channel (auto-detected via sdptool if omitted)")
    args = parser.parse_args()

    channel = args.channel
    if channel is None:
        channel = find_rfcomm_channel(args.address)
        if channel is None:
            parser.error("Could not auto-detect RFCOMM channel; pass -c/--channel explicitly "
                         "(see examples/README.md)")

    printer = BrotherPt.bluetooth(args.address, channel)
    print(f"Media width: {printer.media_width}mm")
    print(f"Media type : {printer.media_type.name}")
    print(f"Tape color : {printer.tape_color.name}")
    print(f"Text color : {printer.text_color.name}")
    printer.close()


if __name__ == "__main__":
    main()
