from __future__ import annotations

import asyncio
import typing

from quorum.cluster.configuration import ClusterConfiguration
from quorum.node.role.leader import Leader

if typing.TYPE_CHECKING:
    from quorum.node.node import Node, INode
from quorum.node.role.role import Role
from quorum.node.role.heartbeat_response import HeartbeatResponse


class BallotBox:
    def __init__(self, electorate: int) -> None:
        self._votes: list[None | bool] = electorate * [None]
        self._current_vote_index = 0
        self._vote_conclusive_event = asyncio.Event()

    def vote(self, vote: bool) -> None:
        self._votes[self._current_vote_index] = vote
        self._current_vote_index += 1
        if self._is_conclusive():
            self._vote_conclusive_event.set()

    @property
    def _majority(self) -> int:
        return (len(self._votes) // 2) + 1

    async def wait_for_vote_conclusive(self) -> None:
        await self._vote_conclusive_event.wait()

    def _is_conclusive(self) -> bool:
        ayes = [vote for vote in self._votes if vote is True]
        nays = [vote for vote in self._votes if vote is False]
        return len(ayes) >= self._majority or len(nays) >= self._majority

    def majority_reached(self) -> bool:
        ayes = [vote for vote in self._votes if vote is True]
        return len(ayes) >= self._majority


class Candidate(Role):
    def __init__(self, node: Node) -> None:
        self._node = node

    async def run(self, other_nodes: set[INode], cluster_configuration: ClusterConfiguration) -> None:
        ballot_box = BallotBox(electorate=len(other_nodes | {self._node}))
        for node in other_nodes | {self._node}:
            asyncio.create_task(self._collect_vote_from(
                ballot_box=ballot_box,
                node=node
            ))

        await ballot_box.wait_for_vote_conclusive()
        if ballot_box.majority_reached():
            self._node.change_role(Leader(self._node))
            return

        from quorum.node.role.subject import Subject
        self._node.change_role(Subject(self._node))

    async def _collect_vote_from(
        self,
        node: INode,
        ballot_box: BallotBox,
    ) -> None:
        if node == self._node:
            ballot_box.vote(True)
        else:
            ballot_box.vote(await node.request_vote())

    def get_node(self) -> Node:
        return self._node

    def heartbeat(self) -> HeartbeatResponse:
        return HeartbeatResponse()

    def stop_running(self) -> None:
        pass

    def request_vote(self) -> bool:
        return False

    def __str__(self) -> str:
        return 'candidate'
