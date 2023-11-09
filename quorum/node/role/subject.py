from __future__ import annotations

import typing

from quorum.cluster.configuration import ClusterConfiguration

if typing.TYPE_CHECKING:
    from quorum.node.node import Node, INode
from quorum.node.role.candidate import Candidate
from quorum.node.role.role import Role
from quorum.node.role.heartbeat_response import HeartbeatResponse


class Subject(Role):
    def __init__(self, node: Node) -> None:
        self._node = node
        self._beaten = False
        self._stopped = False

    async def run(self, other_nodes: set[INode], cluster_configuration: ClusterConfiguration) -> None:
        await cluster_configuration.election_timeout.wait()
        if self._stopped:
            return
        if not self._beaten:
            self._node.change_role(Candidate(self._node))
        self._beaten = False

    def get_node(self) -> Node:
        return self._node

    def heartbeat(self) -> HeartbeatResponse:
        self._beaten = True
        return HeartbeatResponse()

    def stop_running(self) -> None:
        self._stopped = True

    def request_vote(self) -> bool:
        return True

    def __str__(self) -> str:
        return 'subject'
