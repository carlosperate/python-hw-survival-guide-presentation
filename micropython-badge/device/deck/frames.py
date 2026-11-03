# Pre-rendered frames: a pack read whole into RAM, each frame unpacked straight into the display's
# buffer; and the badge's grey frame, kept compressed until it's shown. The formats are in
# character/export.py.
import io
import os
import struct

import deflate
from sticky.display import HEIGHT, WIDTH

GREY = WIDTH * HEIGHT // 4  # bytes in a GS2_HMSB frame


def _inflate(source, buffer):
    """Fill buffer from the zlib stream in source; the bytes filled, fewer if the stream ends."""
    mv = memoryview(buffer)
    n = 0
    with deflate.DeflateIO(source, deflate.ZLIB) as stream:
        while n < len(mv):
            got = stream.readinto(mv[n:])
            if not got:
                break
            n += got
    return n


def _size(source):
    """The bytes in the zlib stream in source, inflated through a 1 KB buffer."""
    buf = bytearray(1024)
    n = 0
    with deflate.DeflateIO(source, deflate.ZLIB) as stream:
        got = stream.readinto(buf)
        while got:
            n += got
            got = stream.readinto(buf)
    return n


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
        if _inflate(source, buffer) < len(buffer):
            raise ValueError("frame %d is short" % i)


class Grey:
    """export.py's badge.gs2, kept compressed; frame() inflates it into a new GS2_HMSB buffer."""

    def __init__(self, path):
        with open(path, "rb") as f:
            self.data = f.read(os.stat(path)[6])
        if self.data[:4] != b"GRY1":
            raise ValueError("not a grey frame: " + path)
        # A damaged file is refused now, not when Up is pressed, without a frame's worth of RAM.
        if _size(self._stream()) != GREY:
            raise ValueError("grey frame of the wrong size: " + path)

    def _stream(self):
        source = io.BytesIO(self.data)
        source.seek(4)
        return source

    def frame(self):
        buffer = bytearray(GREY)
        _inflate(self._stream(), buffer)  # its size was checked when loaded
        return buffer
