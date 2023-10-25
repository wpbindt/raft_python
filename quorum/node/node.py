from __future__ import annotations

from quorum.cluster.configuration import ClusterConfiguration
from quorum.node.role.heartbeat_response import HeartbeatResponse
from quorum.node.role.role import Role


class Node:
    def __init__(self, initial_role: Role) -> None:
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
        new_role.set_node(self)

    async def take_down(self) -> None:
        await self._role.take_down()

    async def bring_back_up(self) -> None:
        await self._role.bring_back_up()

    async def run(self, cluster_configuration: ClusterConfiguration) -> None:
        while True:
            await self._role.run(
                other_nodes=self._other_nodes,
                cluster_configuration=cluster_configuration,
            )

    def heartbeat(self) -> HeartbeatResponse:
        self._role.heartbeat()
