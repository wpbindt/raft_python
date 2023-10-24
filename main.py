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


@dataclass(frozen=True)
class Down:
    pass


Role = Leader | Subject | Down


class Node:
    def __init__(self, initial_role: Role = Leader()) -> None:
        self._role = initial_role

    @property
    def role(self) -> Role:
        return self._role

    async def take_down(self) -> None:
        self._role = Down()

    async def bring_back_up(self) -> None:
        pass


class Cluster:
    def __init__(self, nodes: set[Node]) -> None:
        self._nodes = nodes

    def take_me_to_a_leader(self) -> Node | NoLeaderInCluster:
        current_leaders = {node for node in self._nodes if node.role == Leader()}
        if len(current_leaders) == 0:
            return NoLeaderInCluster()
        if len(current_leaders) > 1:
            raise TooManyLeaders
        return next(iter(current_leaders))


class TooManyLeaders(Exception):
    pass
