from __future__ import annotations

import typing

from quorum.cluster.configuration import ClusterConfiguration
from quorum.node.role.down import Down
from quorum.node.role.leader import Leader

if typing.TYPE_CHECKING:
    from quorum.node.node import Node, INode
from quorum.node.role.role import Role
from quorum.node.role.heartbeat_response import HeartbeatResponse


class Candidate(Role):
    def __init__(self, node: Node) -> None:
        self._node = node

    async def run(self, other_nodes: set[INode], cluster_configuration: ClusterConfiguration) -> None:
        majority = (len(other_nodes | {self}) // 2) + 1
        votes: list[bool] = []
        for node in {self._node} | other_nodes:
            votes.append(await self._request_vote_from(node))
            if sum(votes) < majority:
                continue

            self._node.change_role(Leader(self._node))
            return

        from quorum.node.role.subject import Subject
        self._node.change_role(Subject(self._node))

    async def _request_vote_from(self, node: INode) -> bool:
        if node is self._node:
            return True
        return await node.request_vote()

    def get_node(self) -> Node:
        return self._node

    def heartbeat(self) -> HeartbeatResponse:
        return HeartbeatResponse()

    def stop_running(self) -> None:
        pass

    async def take_down(self) -> None:
        self._node.change_role(Down(previous_role=self))

    async def bring_back_up(self) -> None:
        pass

    async def request_vote(self) -> bool:
        return False

    def __str__(self) -> str:
        return 'candidate'
