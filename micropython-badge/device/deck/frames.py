# Pre-rendered frames: a pack read whole into RAM, each frame unpacked straight into the display's
# buffer. The format is in character/export.py.
import io
import os
import struct

import deflate


class Frames:
    def __init__(self, path):
        with open(path, "rb") as f:
            self.data = f.read(os.stat(path)[6])  # one buffer of the right size, read at once
        if self.data[:4] != b"FRM1":
            raise ValueError("not a frame pack: " + path)
        (count,) = struct.unpack_from("<H", self.data, 4)
        self.offsets = struct.unpack_from("<%dI" % (count + 1), self.data, 6)
        # The last offset is the pack's end: a copy cut short fails here, not mid-animation.
        if self.offsets[-1] != len(self.data):
            raise ValueError("frame pack cut short: " + path)

    def __len__(self):
        return len(self.offsets) - 1

    def unpack(self, i, buffer):
        # BytesIO keeps bytes in place, where it would copy a memoryview; the stream ends itself.
        source = io.BytesIO(self.data)
        source.seek(self.offsets[i])
        mv = memoryview(buffer)
        with deflate.DeflateIO(source, deflate.ZLIB) as stream:
            n = 0
            while n < len(mv):
                got = stream.readinto(mv[n:])
                if not got:
                    raise ValueError("frame %d is short" % i)
                n += got
