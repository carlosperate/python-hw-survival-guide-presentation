import sys

# Run from a checkout of the port (STICKY), so the programme is found from here.
sys.path.insert(0, __file__.rsplit("/", 3)[0] + "/device")
import unittest

from deck.frames import Frames, Grey

# Two 16-byte frames, packed as character/export.py packs them (zlib, 1 KB window).
PACK = (
    b"FRM1\x02\x00\x12\x00\x00\x00*\x00\x00\x008\x00\x00\x00(\xcfc`dbfaec\xe7\xe0\xe4\xe2\xe6"
    b"\xe1\xe5\xe3\x07\x00\x02\xb8\x00y(\xcf\xfb\xff\x1f\x02\x18\xa0\x00\x00c\xac\x07\xf9"
)
PATH = "/tmp/test_frames.frm"
# 96,000 bytes of 0xE4 (levels 0, 1, 2, 3 repeated), as export.py writes badge.gs2; then the same
# one byte short, and one byte long.
EXACT = (
    bytes.fromhex("4752593128cfedc18100000000c3207fcf815ce0085501")
    + bytes(92)
    + bytes.fromhex("7c0398f00f93")
)
SHORT = (
    bytes.fromhex("4752593128cfedc18100000000c3207fcf815ce0085501")
    + bytes(92)
    + bytes.fromhex("5c03895d0eaf")
)
LONG = (
    bytes.fromhex("4752593128cfedc1810000000002a0fd3907596084aa05")
    + bytes(92)
    + bytes.fromhex("f832a8830f93")
)
BADGE = __file__.rsplit("/", 3)[0] + "/device/idle/badge.gs2"


def write(data):
    with open(PATH, "wb") as f:
        f.write(data)


class TestFrames(unittest.TestCase):
    def test_unpacks_each_frame_into_the_buffer(self):
        write(PACK)
        frames = Frames(PATH)
        buffer = bytearray(16)
        self.assertEqual(len(frames), 2)
        frames.unpack(1, buffer)
        self.assertEqual(bytes(buffer), b"\xff" * 8 + b"\x00" * 8)
        frames.unpack(0, buffer)
        self.assertEqual(bytes(buffer), bytes(range(16)))

    def test_a_frame_smaller_than_the_buffer_fails(self):
        write(PACK)
        with self.assertRaises(ValueError):
            Frames(PATH).unpack(0, bytearray(17))

    def test_not_a_pack_fails(self):
        write(b"PNG" + PACK[3:])
        with self.assertRaises(ValueError):
            Frames(PATH)

    # An interrupted copy: refused when loaded, rather than failing on a frame mid-animation.
    def test_a_pack_cut_short_fails(self):
        write(PACK[:-1])
        with self.assertRaises(ValueError):
            Frames(PATH)


class TestGrey(unittest.TestCase):
    # Kept as the file's bytes; each frame() inflates a buffer of its own.
    def test_inflates_one_frame(self):
        write(EXACT)
        grey = Grey(PATH)
        self.assertEqual(grey.data, EXACT)
        frame = grey.frame()
        self.assertEqual(frame, b"\xe4" * 96000)
        self.assertIsNot(grey.frame(), frame)

    # Refused when loaded, not when the badge is first shown.
    def test_a_frame_short_or_long_fails(self):
        for data in (SHORT, LONG):
            write(data)
            with self.assertRaises(ValueError):
                Grey(PATH)

    def test_not_a_grey_frame_fails(self):
        write(b"FRM1" + EXACT[4:])
        with self.assertRaises(ValueError):
            Grey(PATH)

    # The exported badge read as framebuf reads it, at pixels known from its preview, one in
    # each of a byte's four places: QR modules black, its quiet zone white, C1's body light grey,
    # R1's supply trace dark grey, DS1's body black.
    def test_exported_badge_matches_framebuf(self):
        import framebuf

        fb = framebuf.FrameBuffer(Grey(BADGE).frame(), 800, 480, framebuf.GS2_HMSB)
        known = {(646, 321): 0, (649, 321): 0, (642, 317): 3, (644, 259): 2, (628, 100): 1}
        known[(431, 381)] = 0
        for (x, y), level in known.items():
            self.assertEqual(fb.pixel(x, y), level, (x, y))


if __name__ == "__main__":
    unittest.main()
