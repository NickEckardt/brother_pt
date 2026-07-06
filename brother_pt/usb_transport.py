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
from .cmd import USBID_BROTHER, USB_IN_EP_ID, USB_OUT_EP_ID, USB_TRX_TIMEOUT_MS, SupportedPrinterIDs


def find_printers(serial=None):
    # pyusb is only required when actually using the USB transport, so
    # importing this module doesn't force a pyusb dependency on
    # Bluetooth-only users.
    import usb.core

    found_printers = []
    for product_id in SupportedPrinterIDs:
        dev = usb.core.find(idVendor=USBID_BROTHER, idProduct=product_id)
        if dev is not None:
            if serial is not None:
                if serial == dev.serial_number:
                    found_printers.append(dev)
                else:
                    continue
            else:
                found_printers.append(dev)

    return found_printers


class USBTransport:
    def __init__(self, serial: str = None):
        printers = find_printers(serial)
        if len(printers) == 0:
            raise RuntimeError("No supported driver found")

        self._dev = printers[0]
        self.__initialize()

    def __initialize(self):
        # libusb initialization, and bypass kernel drivers
        if self._dev.is_kernel_driver_active(0):
            self._dev.detach_kernel_driver(0)

        self._dev.set_configuration()

    def write(self, data: bytes) -> int:
        length = 0
        while length < len(data):
            # chunk into packet size
            length += self._dev.write(USB_OUT_EP_ID, data[length:(length+0x40)], USB_TRX_TIMEOUT_MS)
            if length == 0:
                raise RuntimeError("IO timeout while writing to printer")
        return length

    def read(self, length: int = 0x80) -> bytes:
        import usb.core
        try:
            data = self._dev.read(USB_IN_EP_ID, length, USB_TRX_TIMEOUT_MS)
        except usb.core.USBError:
            raise RuntimeError("IO timeout while reading from printer")
        return data

    def close(self) -> None:
        import usb.util
        usb.util.dispose_resources(self._dev)
