from __future__ import annotations

import asyncio
import math
from abc import ABC, abstractmethod
from dataclasses import dataclass
from datetime import timedelta
from itertools import count
from random import random
from typing import Iterable

HeartbeatResponse = None


class Role(ABC):
    @abstractmethod
    async def run(self, election_timeout: ElectionTimeout, other_nodes: set[Node], heartbeat_period: timedelta) -> None:
        pass

    @abstractmethod
    def set_node(self, node: Node) -> None:
        pass

    @abstractmethod
    def heartbeat(self) -> HeartbeatResponse:
        pass

    @abstractmethod
    def stop_running(self) -> None:
        pass


@dataclass(frozen=True)
class NoLeaderInCluster:
    pass


class Leader(Role):
    def __init__(self):
        self._stopped = False

    async def run(self, election_timeout: ElectionTimeout, other_nodes: set[Node], heartbeat_period: timedelta) -> None:
        while not self._stopped:
            await asyncio.sleep(heartbeat_period.total_seconds())
            if not self._stopped:
                for node in other_nodes:
                    node.heartbeat()

    def set_node(self, node: Node) -> None:
        pass

    def heartbeat(self) -> HeartbeatResponse:
        pass

    def stop_running(self) -> None:
        self._stopped = True


@dataclass(frozen=True)
class Candidate(Role):
    async def run(self, election_timeout: ElectionTimeout, other_nodes: set[Node], heartbeat_period: timedelta) -> None:
        await asyncio.sleep(math.inf)

    def set_node(self, node: Node) -> None:
        pass

    def heartbeat(self) -> HeartbeatResponse:
        pass

    def stop_running(self) -> None:
        pass


@dataclass
class Subject(Role):
    node: Node | None = None
    beaten: bool = False

    async def run(self, election_timeout: ElectionTimeout, other_nodes: set[Node], heartbeat_period: timedelta) -> None:
        await election_timeout.wait()
        if not self.beaten:
            self.node.change_role(Candidate())

    def set_node(self, node: Node) -> None:
        self.node = node

    def heartbeat(self) -> HeartbeatResponse:
        self.beaten = True

    def stop_running(self) -> None:
        pass


@dataclass(frozen=True)
class Down(Role):
    previous_role: UpRole

    async def run(self, election_timeout: ElectionTimeout, other_nodes: set[Node], heartbeat_period: timedelta) -> None:
        await asyncio.sleep(math.inf)

    def set_node(self, node: Node) -> None:
        pass

    def heartbeat(self) -> HeartbeatResponse:
        pass

    def stop_running(self) -> None:
        pass


UpRole = Leader | Subject | Candidate


class Node:
    def __init__(self, initial_role: Role = Leader()) -> None:
        self._role = initial_role
        self._role.set_node(self)
        self._other_nodes: set[Node] = set()

    def register_node(self, node: Node) -> None:
        if node != self:
            self._other_nodes.add(node)

    @property
    def role(self) -> Role:
        return self._role

    def change_role(self, new_role: Role) -> None:
        self._role.stop_running()
        self._role = new_role

    async def take_down(self) -> None:
        if isinstance(self._role, (Leader, Subject, Candidate)):
            self.change_role(Down(self._role))

    async def bring_back_up(self) -> None:
        if isinstance(self._role, Down):
            self.change_role(self._role.previous_role)

    async def run(self, election_timeout: ElectionTimeout, heartbeat_period: timedelta) -> None:
        while True:
            await self._role.run(
                election_timeout=election_timeout,
                other_nodes=self._other_nodes,
                heartbeat_period=heartbeat_period,
            )

    def heartbeat(self) -> HeartbeatResponse:
        self._role.heartbeat()


@dataclass(frozen=True)
class ClusterConfiguration:
    election_timeout: ElectionTimeout
    heartbeat_period: timedelta


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
        cluster_configuration: ClusterConfiguration,
    ) -> None:
        self._nodes = nodes
        for node in self._nodes:
            for other_node in self._nodes:
                node.register_node(other_node)
        self._election_timeout = cluster_configuration.election_timeout
        self._heartbeat_period = cluster_configuration.heartbeat_period

    def take_me_to_a_leader(self) -> Node | NoLeaderInCluster:
        current_leaders = {node for node in self._nodes if isinstance(node.role, Leader)}
        if len(current_leaders) == 0:
            return NoLeaderInCluster()
        if len(current_leaders) > 1:
            raise TooManyLeaders
        return next(iter(current_leaders))

    async def run(self) -> None:
        await asyncio.gather(*[node.run(self._election_timeout, self._heartbeat_period) for node in self._nodes])


class TooManyLeaders(Exception):
    pass
