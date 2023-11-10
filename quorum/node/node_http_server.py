import asyncio
import math
from datetime import timedelta

from fastapi import FastAPI
from starlette.requests import Request
from starlette.responses import JSONResponse
from uvicorn import Server, Config

from quorum.cluster.configuration import ClusterConfiguration, ElectionTimeout
from quorum.node.node import Node


class NodeServer:
    def __init__(
        self,
        node: Node[str],
        cluster_configuration: ClusterConfiguration,
    ) -> None:
        self._node = node
        self._cluster_configuration = cluster_configuration

    async def run(self, port: int) -> None:
        asyncio.create_task(self._node.run(self._cluster_configuration))
        app = FastAPI()
        app.add_route(
            path='/heartbeat',
            route=self.heartbeat,
            methods=['POST']
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
