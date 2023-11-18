import asyncio
from typing import Iterable

from starlette.applications import Starlette
from starlette.requests import Request
from starlette.responses import JSONResponse
from starlette.routing import Route
from uvicorn import Server, Config

from quorum.cluster.configuration import ClusterConfiguration
from quorum.node.node import Node, INode


class NodeServer:
    def __init__(
        self,
        node: Node[str],
        remote_nodes: Iterable[INode[str]],
        cluster_configuration: ClusterConfiguration,
    ) -> None:
        self._node = node
        self._cluster_configuration = cluster_configuration
        for remote_node in remote_nodes:
            self._node.register_node(remote_node)

    async def run(self, port: int) -> None:
        asyncio.create_task(self._node.run(self._cluster_configuration))
        app = Starlette(
            routes=[
                Route(path='/heartbeat', endpoint=self.heartbeat, methods=['POST']),
                Route(path='/request_vote', endpoint=self.request_vote, methods=['POST']),
                Route(path='/send_message', endpoint=self.send_message, methods=['POST']),
                Route(path='/get_messages', endpoint=self.get_messages, methods=['GET']),
            ]
        )
        server = Server(config=Config(host='0.0.0.0', port=port, app=app))

        try:
            await server.serve()
        except asyncio.CancelledError:
            await server.shutdown()
            raise

    async def heartbeat(self, request: Request) -> JSONResponse:
        await self._node.heartbeat()
        return JSONResponse(status_code=200, content='')

    async def request_vote(self, request: Request) -> JSONResponse:
        vote = await self._node.request_vote()
        return JSONResponse(status_code=200, content={'vote': vote})

    async def send_message(self, request: Request) -> JSONResponse:
        await self._node.send_message((await request.json())['message'])
        return JSONResponse(status_code=200, content='')

    async def get_messages(self, request: Request) -> JSONResponse:
        messages = await self._node.get_messages()
        return JSONResponse(status_code=200, content={'messages': list(messages)})
