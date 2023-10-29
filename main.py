import asyncio
import sys
from datetime import timedelta
from typing import NoReturn

from quorum.cluster.cluster import Cluster
from quorum.cluster.configuration import ClusterConfiguration, ElectionTimeout
from quorum.node.node import Node
from quorum.node.role.subject import Subject


def print_cluster(cluster: Cluster) -> int:
    to_print = str(cluster)
    print(cluster)
    return len(to_print.split('\n'))


async def main() -> NoReturn:
    nodes = {
        Node(lambda node: Subject(node))
        for _ in range(5)
    }
    cluster = Cluster(
        nodes=nodes,
        cluster_configuration=ClusterConfiguration(
            election_timeout=ElectionTimeout(
                min_timeout=timedelta(seconds=4),
                max_timeout=timedelta(seconds=5),
            ),
            heartbeat_period=timedelta(seconds=2),
        )
    )
    asyncio.create_task(cluster.run())
    lines_printed = print_cluster(cluster)
    while True:
        sys.stdout.write(lines_printed * "\033[F")
        lines_printed = print_cluster(cluster)
        await asyncio.sleep(0.05)

if __name__ == '__main__':
    asyncio.run(main())
