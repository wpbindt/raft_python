import aiohttp

from quorum.node.node_interface import INode
from quorum.node.role.heartbeat_response import HeartbeatResponse


class NodeHttpClient(INode[str]):
    def __init__(self, url: str) -> None:
        self._url = url
        self._client_session = aiohttp.ClientSession()

    async def request_vote(self) -> bool:
        async with self._client_session.post(f'{self._url}/request_vote') as response:
            response_data = await response.json()
        return bool(response_data['vote'])

    async def heartbeat(self) -> HeartbeatResponse:
        async with self._client_session.post(f'{self._url}/heartbeat') as response:
            await response.json()
        return HeartbeatResponse()

    async def send_message(self, message: str) -> None:
        async with self._client_session.post(
            f'{self._url}/send_message',
            json={'message': message},
            headers={'Content-Type': 'application/json'},
        ) as response:
            await response.json()

    async def get_messages(self) -> tuple[str, ...]:
        async with self._client_session.get(f'{self._url}/get_messages') as response:
            response_data = await response.json()
        return tuple(response_data['messages'])

    def _get_id(self) -> int:
        return hash(self._url)
