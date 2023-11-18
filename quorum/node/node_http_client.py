import aiohttp

from quorum.node.node import INode
from quorum.node.role.heartbeat_response import HeartbeatResponse


class NodeHttpClient(INode[str]):
    def __init__(self, url: str) -> None:
        self._url = url

    async def request_vote(self) -> bool:
        async with aiohttp.ClientSession() as client:
            response = await client.post(f'{self._url}/request_vote')
            response_data = await response.json()
        return response_data['vote']

    async def heartbeat(self) -> HeartbeatResponse:
        async with aiohttp.ClientSession() as client:
            await client.post(f'{self._url}/heartbeat')
        return HeartbeatResponse()

    async def send_message(self, message: str) -> None:
        async with aiohttp.ClientSession() as client:
            await client.post(
                f'{self._url}/send_message',
                json={'message': message},
                headers={'Content-Type': 'application/json'},
            )

    async def get_messages(self) -> tuple[str, ...]:
        async with aiohttp.ClientSession() as client:
            response = await client.get(f'{self._url}/get_messages')
            response_data = await response.json()
        return tuple(response_data['messages'])

    def get_id(self) -> int:
        pass
