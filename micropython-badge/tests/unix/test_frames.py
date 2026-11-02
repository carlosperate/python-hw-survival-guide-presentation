import sys

# Run from a checkout of the port (STICKY), so the programme is found from here.
sys.path.insert(0, __file__.rsplit("/", 3)[0] + "/device")
import unittest

from deck.frames import Frames

# Two 16-byte frames, packed as character/export.py packs them (zlib, 1 KB window).
PACK = (
    b"FRM1\x02\x00\x12\x00\x00\x00*\x00\x00\x008\x00\x00\x00(\xcfc`dbfaec\xe7\xe0\xe4\xe2\xe6"
    b"\xe1\xe5\xe3\x07\x00\x02\xb8\x00y(\xcf\xfb\xff\x1f\x02\x18\xa0\x00\x00c\xac\x07\xf9"
)
PATH = "/tmp/test_frames.frm"


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


if __name__ == "__main__":
    unittest.main()
