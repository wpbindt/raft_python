from __future__ import annotations

import asyncio
import math
from dataclasses import dataclass
from datetime import timedelta
from typing import NoReturn


@dataclass(frozen=True)
class NoLeaderInCluster:
    pass


@dataclass(frozen=True)
class Leader:
    pass


@dataclass(frozen=True)
class Candidate:
    pass


@dataclass(frozen=True)
class Subject:
    pass


@dataclass(frozen=True)
class Down:
    previous_role: UpRole


UpRole = Leader | Subject | Candidate
Role = UpRole | Down


class Node:
    def __init__(self, initial_role: Role = Leader()) -> None:
        self._role = initial_role

    @property
    def role(self) -> Role:
        return self._role

    async def take_down(self) -> None:
        if not isinstance(self._role, Down):
            self._role = Down(self._role)

    async def bring_back_up(self) -> None:
        if isinstance(self._role, Down):
            self._role = self._role.previous_role


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
        await asyncio.sleep(self._election_timeout.total_seconds())
        for node in self._nodes:
            node._role = Candidate()
        await asyncio.sleep(math.inf)


class TooManyLeaders(Exception):
    pass
