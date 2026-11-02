# The deck's protocol on the BLE UART: newline-terminated states, the newest complete line wins.
# Gives the player the changed() and state it reads.

import asyncio

MAX_LINE = 64


class Lines:
    def __init__(self, uart):
        self.uart = uart
        self.state = b""
        self._new = asyncio.Event()  # set by run(), a task: a ThreadSafeFlag would be polled

    async def run(self):
        reader = asyncio.StreamReader(self.uart)
        partial = b""
        gaps = self.uart.gaps
        while True:
            data = await reader.read(MAX_LINE)
            # A new connection or a loss: the fragment held from before mustn't prefix a new line.
            if self.uart.gaps != gaps:
                gaps = self.uart.gaps
                partial = b""
            *lines, partial = (partial + data).split(b"\n")
            # Kept just past the limit, so a line too long is refused whole, end included.
            partial = partial[: MAX_LINE + 1]
            for line in reversed(lines):
                state = line.strip()
                if state and len(line) <= MAX_LINE:
                    self.state = state
                    self._new.set()
                    break

    @property
    def connected(self):
        return self.uart.connected

    async def changed(self):
        await self._new.wait()
        self._new.clear()
        return self.state

    def notify(self, data):
        return self.uart.write(data + b"\n")

    # The deck owns the radio here, so stopping it is the deck's call.
    def close(self):
        import bluetooth

        self.uart.close()
        bluetooth.BLE().active(False)
