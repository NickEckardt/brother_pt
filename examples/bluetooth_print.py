#!/usr/bin/env python3
"""Print a text label to a Brother PT printer over Bluetooth RFCOMM.

Requires the printer to already be paired/bonded (e.g. via `bluetoothctl`).

Usage:
    python3 bluetooth_print.py <bdaddr> --text "Hello" [-c CHANNEL] [--no-half-cut]

If -c/--channel is omitted, the RFCOMM channel is looked up automatically
via `sdptool browse <bdaddr>`. See examples/README.md if that lookup fails.

By default this adds a leading score cut (peel tab) before the label, in
addition to the trailing separating cut -- pass --no-half-cut to disable it
and use plain auto-cut instead. Only verified on a PT-E560BT -- results may
differ on other printer models. Note: on the PT-E560BT, plain auto-cut
(--no-half-cut) was found to waste a blank leading piece of tape before the
real content; half-cut mode does not have this problem, which is why it's
the default here despite being the more elaborate option.
"""
import argparse
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from brother_pt.printer import BrotherPt
from brother_pt.bluetooth_transport import find_rfcomm_channel
from brother_pt.cmd import MediaWidthToTapeMargin
from PIL import Image, ImageDraw, ImageFont

NARROW_FONT = "/usr/share/fonts/truetype/liberation/LiberationSansNarrow-Regular.ttf"


def build_label(print_height: int, text: str) -> Image.Image:
    font = ImageFont.truetype(NARROW_FONT, size=int(print_height * 0.55))
    tmp = Image.new('L', (10, 10), color=255)
    d = ImageDraw.Draw(tmp)
    bbox = d.textbbox((0, 0), text, font=font)
    text_w = bbox[2] - bbox[0]
    text_h = bbox[3] - bbox[1]

    width = text_w + 10
    img = Image.new('L', (width, print_height), color=255)
    d = ImageDraw.Draw(img)
    x = (width - text_w) // 2 - bbox[0]
    y = (print_height - text_h) // 2 - bbox[1]
    d.text((x, y), text, font=font, fill=0)
    return img


def main():
    parser = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("address", help="Bluetooth device address, e.g. 94:DD:F8:A1:9E:98")
    parser.add_argument("-c", "--channel", type=int, default=None,
                         help="RFCOMM channel (auto-detected via sdptool if omitted)")
    parser.add_argument("--text", required=True, help="Text to print on the label")
    parser.add_argument("--margin", type=int, default=20, help="Feed margin in dots")
    parser.add_argument("--no-half-cut", dest="half_cut", action="store_false", default=True,
                         help="Disable the leading peel-tab score cut and use plain auto-cut instead")
    args = parser.parse_args()

    channel = args.channel
    if channel is None:
        channel = find_rfcomm_channel(args.address)
        if channel is None:
            parser.error("Could not auto-detect RFCOMM channel; pass -c/--channel explicitly "
                         "(see examples/README.md)")

    printer = BrotherPt.bluetooth(args.address, channel)
    print(f"Connected. Media width: {printer.media_width}mm, type: {printer.media_type.name}")

    print_height = MediaWidthToTapeMargin.to_print_width(printer.media_width)
    label = build_label(print_height, args.text)
    print(f"Label image size: {label.size}")

    printer.print_image(label, margin_px=args.margin, half_cut=args.half_cut)
    print("Print job completed.")
    printer.close()


if __name__ == "__main__":
    main()
