import asyncio
import random
import sys
from datetime import timedelta
from typing import NoReturn

from quorum.cluster.cluster import Cluster
from quorum.cluster.configuration import ClusterConfiguration, ElectionTimeout
from quorum.node.node import Node
from quorum.node.role.leader import Leader
from quorum.node.role.subject import Subject


def print_cluster(cluster: Cluster) -> int:
    to_print = str(cluster)
    print(cluster)
    return len(to_print.split('\n'))


async def randomly_take_stuff_down(nodes: set[Node]) -> NoReturn:
    while True:
        await asyncio.sleep(1 + random.random())
        node = random.choice(list(node for node in nodes if isinstance(node.role, Leader)))
        await node.pause()
        await asyncio.sleep(2 + random.random())
        await node.unpause()


async def main() -> NoReturn:
    nodes: set[Node[str]] = {
        Node(lambda node: Subject(node))
        for _ in range(5)
    }
    cluster = Cluster[str](
        nodes=nodes,
        cluster_configuration=ClusterConfiguration(
            election_timeout=ElectionTimeout(
                min_timeout=timedelta(seconds=0.150),
                max_timeout=timedelta(seconds=0.2),
            ),
            heartbeat_period=timedelta(seconds=0.01),
        )
    )
    asyncio.create_task(cluster.run())
    asyncio.create_task(randomly_take_stuff_down(nodes))
    lines_printed = print_cluster(cluster)
    while True:
        sys.stdout.write(lines_printed * "\033[F")
        lines_printed = print_cluster(cluster)
        await asyncio.sleep(0.05)

if __name__ == '__main__':
    asyncio.run(main())
