from dataclasses import dataclass


@dataclass(frozen=True)
class NoLeader:
    pass


class Node:
    pass


class Cluster:
    def __init__(self, nodes: set[Node]) -> None:
        self._nodes = nodes

    def take_me_to_a_leader(self) -> Node | NoLeader:
        return NoLeader()
