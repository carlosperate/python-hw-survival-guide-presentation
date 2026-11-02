# The fake link and protocol the player's tests share, on the unix port and on the board.
import asyncio


class Link:
    """The members the player and run() use, fed by the test."""

    connected = True

    def __init__(self):
        self.state = b""
        self._flag = asyncio.ThreadSafeFlag()

    def send(self, state):
        self.state = state
        self._flag.set()

    async def changed(self):
        await self._flag.wait()
        return self.state

    async def run(self):
        pass

    def close(self):
        self.closed = True


def parse(state):
    name, _, step = state.decode().partition(" ")
    return name, int(step or 0)
