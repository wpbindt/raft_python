import asyncio
from dataclasses import dataclass
from datetime import timedelta
from itertools import count
from random import random
from typing import Iterable


class ElectionTimeout:
    def __init__(
            self,
            max_timeout: timedelta,
            min_timeout: timedelta = timedelta(seconds=0),
            randomization: Iterable[float] = (random() for _ in count()),
    ) -> None:
        self._min_timeout = min_timeout
        self._max_timeout = max_timeout
        self._randomization = iter(randomization)

    async def wait(self) -> None:
        boh = self._min_timeout + next(self._randomization) * (self._max_timeout - self._min_timeout)
        await asyncio.sleep(boh.total_seconds())


@dataclass(frozen=True)
class ClusterConfiguration:
    election_timeout: ElectionTimeout
    heartbeat_period: timedelta
