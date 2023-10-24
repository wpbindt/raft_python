from __future__ import annotations

import asyncio
import math
from abc import ABC, abstractmethod
from dataclasses import dataclass
from datetime import timedelta
from itertools import count
from random import random
from typing import Iterable


class Role(ABC):
    @abstractmethod
    async def run(self, election_timeout: ElectionTimeout) -> None:
        pass

    @abstractmethod
    def set_node(self, node: Node) -> None:
        pass


@dataclass(frozen=True)
class NoLeaderInCluster:
    pass


@dataclass(frozen=True)
class Leader(Role):
    async def run(self, election_timeout: ElectionTimeout) -> None:
        await asyncio.sleep(math.inf)

    def set_node(self, node: Node) -> None:
        pass


@dataclass(frozen=True)
class Candidate(Role):
    async def run(self, election_timeout: ElectionTimeout) -> None:
        await asyncio.sleep(math.inf)

    def set_node(self, node: Node) -> None:
        pass


@dataclass
class Subject(Role):
    node: Node | None = None

    async def run(self, election_timeout: ElectionTimeout) -> None:
        await election_timeout.wait()
        self.node.change_role(Candidate())

    def set_node(self, node: Node) -> None:
        self.node = node


@dataclass(frozen=True)
class Down(Role):
    previous_role: UpRole

    async def run(self, election_timeout: ElectionTimeout) -> None:
        await asyncio.sleep(math.inf)

    def set_node(self, node: Node) -> None:
        pass


UpRole = Leader | Subject | Candidate


class Node:
    def __init__(self, initial_role: Role = Leader()) -> None:
        self._role = initial_role
        self._role.set_node(self)

    @property
    def role(self) -> Role:
        return self._role

    def change_role(self, new_role: Role) -> None:
        self._role = new_role

    async def take_down(self) -> None:
        if isinstance(self._role, (Leader, Subject, Candidate)):
            self._role = Down(self._role)

    async def bring_back_up(self) -> None:
        if isinstance(self._role, Down):
            self._role = self._role.previous_role

    async def run(self, election_timeout: ElectionTimeout) -> None:
        await self._role.run(election_timeout)


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


class Cluster:
    def __init__(
        self,
        nodes: set[Node],
        election_timeout: ElectionTimeout = ElectionTimeout(timedelta(days=1)),
    ) -> None:
        self._nodes = nodes
        self._election_timeout = election_timeout

    def take_me_to_a_leader(self) -> Node | NoLeaderInCluster:
        current_leaders = {node for node in self._nodes if node.role == Leader()}
        if len(current_leaders) == 0:
            return NoLeaderInCluster()
        if len(current_leaders) > 1:
            raise TooManyLeaders
        return next(iter(current_leaders))

    async def run(self) -> None:
        await asyncio.gather(*[node.run(self._election_timeout) for node in self._nodes])


class TooManyLeaders(Exception):
    pass
