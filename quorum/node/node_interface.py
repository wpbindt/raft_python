from abc import ABC, abstractmethod
from typing import Generic, Any

from quorum.cluster.message_type import MessageType
from quorum.node.role.heartbeat_response import HeartbeatResponse


class PublicNode(ABC, Generic[MessageType]):
    @abstractmethod
    async def send_message(self, message: MessageType) -> None:
        pass

    @abstractmethod
    async def get_messages(self) -> tuple[MessageType, ...]:
        pass


class InternalNode(ABC, Generic[MessageType]):
    @abstractmethod
    async def request_vote(self) -> bool:
        pass

    @abstractmethod
    async def heartbeat(self) -> HeartbeatResponse:
        pass

    @abstractmethod
    async def send_message(self, message: MessageType) -> None:
        pass

    @abstractmethod
    async def get_messages(self) -> tuple[MessageType, ...]:
        pass

    @abstractmethod
    def _get_id(self) -> int:
        pass

    def __eq__(self, other: Any) -> bool:
        if not isinstance(other, InternalNode):
            return False
        return self._get_id() == other._get_id()

    def __hash__(self) -> int:
        return hash(self._get_id())
