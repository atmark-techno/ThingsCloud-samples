import asyncio
from abc import ABC, abstractmethod
from time import time


class Loopable(ABC):
    @abstractmethod
    async def routine(self):
        pass

    def __init__(self, interval):
        self.interval = interval

    async def __async_loop(self, timeout=None):
        if timeout is not None:
            started_at = int(time())

        while True:
            loop_started_at = int(time())

            await self.routine()

            now = int(time())
            if timeout is not None and now - started_at >= timeout:
                break

            interval = self.interval - (now - loop_started_at)
            await asyncio.sleep(max(interval, 0))

    def start_loop(self, timeout=None):
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        loop.run_until_complete(self.__async_loop(timeout))
