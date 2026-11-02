import sys

# Run from a checkout of the port (STICKY), so the programme is found from here.
sys.path.insert(0, __file__.rsplit("/", 3)[0] + "/device")
# The name the badge advertises, on the board's radio: the deck's chooser filters on its prefix.
import unittest

import bluetooth
from deck.app import NAME_PREFIX, link_name
from sticky.bleuart import BLEUART


class TestLink(unittest.TestCase):
    def test_advertises_as_the_badge(self):
        ble = bluetooth.BLE()
        uart = None
        try:
            ble.active(True)
            name = link_name(ble)
            self.assertTrue(name.startswith(NAME_PREFIX))
            self.assertEqual(len(name), len(NAME_PREFIX) + 4)
            uart = BLEUART(name)
            gap_name = ble.config("gap_name")
            if isinstance(gap_name, bytes):
                gap_name = gap_name.decode()
            self.assertEqual(gap_name, name)
        finally:
            if uart is not None:
                uart.close()
            ble.active(False)


if __name__ == "__main__":
    unittest.main()
