from __future__ import annotations

import asyncio
import math
from abc import ABC, abstractmethod
from dataclasses import dataclass
from datetime import timedelta
from typing import NoReturn


class Role(ABC):
    @abstractmethod
    async def run(self, election_timeout: timedelta) -> NoReturn:
        pass

    @abstractmethod
    def set_node(self, node: Node) -> None:
        pass


@dataclass(frozen=True)
class NoLeaderInCluster:
    pass


@dataclass(frozen=True)
class Leader(Role):
    async def run(self, election_timeout: timedelta) -> NoReturn:
        await asyncio.sleep(math.inf)

    def set_node(self, node: Node) -> None:
        pass


@dataclass(frozen=True)
class Candidate(Role):
    async def run(self, election_timeout: timedelta) -> NoReturn:
        await asyncio.sleep(math.inf)

    def set_node(self, node: Node) -> None:
        pass


@dataclass
class Subject(Role):
    node: Node | None = None

    async def run(self, election_timeout: timedelta) -> NoReturn:
        await asyncio.sleep(election_timeout.total_seconds())
        self.node.change_role(Candidate())

    def set_node(self, node: Node) -> None:
        self.node = node


@dataclass(frozen=True)
class Down(Role):
    previous_role: UpRole

    async def run(self, election_timeout: timedelta) -> NoReturn:
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
        if isinstance(self._role, UpRole):
            self._role = Down(self._role)

    async def bring_back_up(self) -> None:
        if isinstance(self._role, Down):
            self._role = self._role.previous_role

    async def run(self, election_timeout: timedelta) -> NoReturn:
        await self._role.run(election_timeout)


class Cluster:
    def __init__(
        self,
        nodes: set[Node],
        election_timeout: timedelta = timedelta(days=1),
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

    async def run(self) -> NoReturn:
        await asyncio.gather(*[node.run(self._election_timeout) for node in self._nodes])


class TooManyLeaders(Exception):
    pass
