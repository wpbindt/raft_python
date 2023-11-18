import aiohttp

from quorum.cluster.message_type import MessageType
from quorum.node.node import INode
from quorum.node.role.heartbeat_response import HeartbeatResponse


class NodeHttpClient(INode[str]):
    def __init__(self, url: str) -> None:
        self._url = url

    def register_node(self, node: INode) -> None:
        raise NotImplementedError

    async def request_vote(self) -> bool:
        async with aiohttp.ClientSession() as client:
            response = await client.post(f'{self._url}/request_vote')
            response.raise_for_status()
            response_data = await response.json()
        return response_data['vote']

    async def heartbeat(self) -> HeartbeatResponse:
        async with aiohttp.ClientSession() as client:
            await client.post(f'{self._url}/heartbeat')
        return HeartbeatResponse()

    async def send_message(self, message: MessageType) -> None:
        async with aiohttp.ClientSession() as client:
            await client.post(
                f'{self._url}/send_message',
                json={'message': message},
                headers={'Content-Type': 'application/json'},
            )

    async def get_messages(self) -> tuple[MessageType, ...]:
        pass

    def get_id(self) -> int:
        pass
