from dataclasses import dataclass


@dataclass(frozen=True)
class NoLeaderInCluster:
    pass


@dataclass(frozen=True)
class Leader:
    pass


@dataclass(frozen=True)
class Subject:
    pass


Role = Leader | Subject


class Node:
    def __init__(self, initial_role: Role = Leader()) -> None:
        self._initial_role = initial_role

    @property
    def role(self) -> Role:
        return self._initial_role


class Cluster:
    def __init__(self, nodes: set[Node]) -> None:
        self._nodes = nodes

    @property
    def _leaders(self) -> set[Node]:
        return {node for node in self._nodes if node.role == Leader()}

    def take_me_to_a_leader(self) -> Node | NoLeaderInCluster:
        if len(self._leaders) > 0:
            return next(iter(self._leaders))
        return NoLeaderInCluster()
