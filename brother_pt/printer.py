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
import sys
import warnings

from .cmd import *
from .raster import *
from .usb_transport import USBTransport
from .bluetooth_transport import BluetoothTransport


class BrotherPt:
    def __init__(self, transport):
        self._transport = transport

        self._media_width = None
        self._media_type = None
        self._tape_color = None
        self._text_color = None

        self.update_status()

    @classmethod
    def usb(cls, serial: str = None) -> "BrotherPt":
        return cls(USBTransport(serial))

    @classmethod
    def bluetooth(cls, address: str, channel: int = 1) -> "BrotherPt":
        return cls(BluetoothTransport(address, channel))

    def close(self) -> None:
        self._transport.close()

    def __write(self, data: bytes) -> int:
        return self._transport.write(data)

    def __read(self, length: int = 0x80) -> bytes:
        return self._transport.read(length)

    def update_status(self):
        self.__write(invalidate())
        self.__write(initialize())
        status_information = b''
        while len(status_information) == 0:
            self.__write(status_information_request())
            status_information = self.__read(STATUS_MESSAGE_LENGTH)

        self._media_width = status_information[StatusOffsets.MEDIA_WIDTH]
        self._media_type = MediaType(status_information[StatusOffsets.MEDIA_TYPE])
        self._tape_color = TapeColor(status_information[StatusOffsets.TAPE_COLOR_INFORMATION])
        self._text_color = TextColor(status_information[StatusOffsets.TEXT_COLOR_INFORMATION])

    @property
    def media_width(self) -> int:
        return self._media_width

    @property
    def media_type(self) -> MediaType:
        return self._media_type

    @property
    def tape_color(self) -> TapeColor:
        return self._tape_color

    @property
    def text_color(self) -> TextColor:
        return self._text_color

    def print_data(self, data: bytes, margin_px: int, half_cut: bool = True):
        advanced_mode = AdvancedMode.NO_CHAINING
        mode = Mode.AUTO_CUT
        if half_cut:
            # Verified on a PT-E560BT: HALF_CUT + CUT_ON_LAST_LABEL with AUTO_CUT off
            # produces a leading score cut (peel tab) plus the trailing separating cut,
            # with no wasted blank leading cut. The plain AUTO_CUT/NO_CHAINING path
            # (half_cut=False) was found to feed and fully cut a wasted blank leading
            # piece before the real content -- true even with pristine, unmodified
            # upstream code, so it isn't something introduced by this library. Default
            # to half_cut=True since it's the only mode that avoids that waste.
            # Unverified on other printer models.
            advanced_mode |= AdvancedMode.HALF_CUT | AdvancedMode.CUT_ON_LAST_LABEL
            mode = Mode(0)
        self.__write(enter_dynamic_command_mode())
        self.__write(enable_status_notification())
        self.__write(print_information(data, self.media_width))
        self.__write(set_mode(mode))
        self.__write(set_advanced_mode(advanced_mode))
        self.__write(margin_amount(margin_px))
        self.__write(set_compression_mode())
        for cmd in gen_raster_commands(data):
            self.__write(cmd)
        self.__write(print_with_feeding())
        while True:
            res = self.__read()
            if len(res) > 0:
                if res[StatusOffsets.STATUS_TYPE] == StatusType.PRINTING_COMPLETED:
                    # absorb phase change message, if any -- not all transports/models send one
                    try:
                        self.__read()
                    except RuntimeError:
                        pass
                    break
                elif res[StatusOffsets.STATUS_TYPE] == StatusType.ERROR_OCCURRED:
                    error_message = ''
                    if res[8]: # Error 1
                        if res[8] & 0x01:
                            error_message += 'no media|'
                        if res[8] & 0x04:
                            error_message += 'cutter jam|'
                        if res[8] & 0x08:
                            error_message += 'low batteries|'
                        if res[8] & 0x40:
                            error_message += 'high-voltage adapter|'
                        pass
                    if res[9]: # Error 2
                        if res[9] & 0x01:
                            error_message += 'wrong media (check size)|'
                        if res[9] & 0x10:
                            error_message += 'cover open|'
                        if res[9] & 0x20:
                            error_message += 'overheating|'
                    if len(error_message) > 0:
                        error_message = error_message[:-1]
                    raise RuntimeError(error_message)

    def print_image(self, image: Image, margin_px: int = 0, half_cut: bool = True):
        self.update_status()
        image = prepare_image(image, self.media_width)
        if (image.width + margin_px) < MINIMUM_TAPE_POINTS:
            warnings.warn("Image (%i) + cut margin (%i) is smaller than minimum tape width (%i) ... "
                          "cutting length will be extended" % (image.width, margin_px, MINIMUM_TAPE_POINTS))
        data = raster_image(image, self.media_width)
        self.print_data(data, margin_px, half_cut)


if __name__ == '__main__':
    printer = BrotherPt.usb()
    print("Media width: %dmm" % printer.media_width)
    print("Media type : %s" % printer.media_type.name)
    print("Tape color : %s" % printer.tape_color.name)
    print("Text color : %s" % printer.text_color.name)
    print()
    if len(sys.argv) != 2:
        print("%s <imagename>" % sys.argv[0], file=sys.stderr)
        sys.exit(1)
    image = Image.open(sys.argv[1])

    printer.print_image(image)
