from __future__ import annotations

import typing

from quorum.cluster.configuration import ClusterConfiguration
from quorum.cluster.message_type import MessageType

if typing.TYPE_CHECKING:
    from quorum.node.node import Node
    from quorum.node.node_interface import InternalNode
from quorum.node.role.candidate import Candidate
from quorum.node.role.role import Role
from quorum.node.role.heartbeat_response import HeartbeatResponse


class Subject(Role[MessageType], typing.Generic[MessageType]):
    def __init__(self, node: Node[MessageType]) -> None:
        self._node = node
        self._beaten = False
        self._stopped = False
        self._voted = False

    async def run(
        self,
        other_nodes: set[InternalNode[MessageType]],
        cluster_configuration: ClusterConfiguration,
    ) -> None:
        await cluster_configuration.election_timeout.wait()
        if self._stopped:
            return
        if not self._beaten:
            self._node.change_role(Candidate(self._node))
        self._beaten = False

    def heartbeat(self) -> HeartbeatResponse:
        self._beaten = True
        self._voted = False
        return HeartbeatResponse()

    def stop_running(self) -> None:
        self._stopped = True

    def request_vote(self) -> bool:
        vote = not self._voted
        self._voted = True
        return vote

    def __str__(self) -> str:
        return 'subject'
