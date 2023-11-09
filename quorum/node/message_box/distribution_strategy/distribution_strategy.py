from __future__ import annotations
import typing
from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Generic

from quorum.cluster.message_type import MessageType
if typing.TYPE_CHECKING:
    from quorum.node.node import Node


class DistributionStrategy(ABC, Generic[MessageType]):
    @abstractmethod
    async def distribute(self, message: MessageType, other_nodes: set[Node[MessageType]]) -> DistributionSuccessful | DistributionFailed:
        pass


@dataclass(frozen=True)
class DistributionSuccessful:
    pass


@dataclass(frozen=True)
class DistributionFailed:
    pass
