from __future__ import annotations

import asyncio
from datetime import timedelta

from quorum.cluster.cluster import Cluster
from quorum.cluster.configuration import ClusterConfiguration, ElectionTimeout
from quorum.node.node import Node, DownableNode
from quorum.node.role.candidate import Candidate
from quorum.node.role.leader import Leader
from quorum.node.role.subject import Subject


def get_frozen_cluster(
    nodes: set[DownableNode],
    election_timeout: ElectionTimeout = ElectionTimeout(timedelta(seconds=1)),
    heartbeat_period: timedelta = timedelta(seconds=1),
) -> Cluster[str]:
    return Cluster[str](
        nodes=nodes,
        cluster_configuration=ClusterConfiguration(
            election_timeout=election_timeout,
            heartbeat_period=heartbeat_period,
        ),
    )


async def get_running_cluster(
    nodes: set[DownableNode],
    election_timeout: ElectionTimeout = ElectionTimeout(timedelta(seconds=1)),
    heartbeat_period: timedelta = timedelta(seconds=1),
) -> Cluster[str]:
    cluster = get_frozen_cluster(
        nodes=nodes,
        election_timeout=election_timeout,
        heartbeat_period=heartbeat_period,
    )
    asyncio.create_task(cluster.run())
    return cluster


def create_subject_node() -> DownableNode:
    return DownableNode(Node(lambda node: Subject(node)))


def create_leader_node() -> DownableNode:
    return DownableNode(Node(lambda node: Leader(node)))


def create_candidate_node() -> DownableNode:
    return DownableNode(Node(lambda node: Candidate(node)))
