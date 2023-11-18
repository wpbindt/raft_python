import asyncio
import logging
import math
import sys
from datetime import timedelta

from quorum.cluster.configuration import ClusterConfiguration, ElectionTimeout
from quorum.node.node import Node
from quorum.node.node_http_client import NodeHttpClient
from quorum.node.node_http_server import NodeServer
from quorum.node.role.subject import Subject


async def main():
    urls = sys.argv[1:-1]
    port = int(sys.argv[-1])
    remote_clients = [
        NodeHttpClient(url)
        for url in urls
    ]
    local_node = Node(lambda node: Subject(node))

    logger = logging.getLogger()
    if len(logger.handlers) == 0:
        handler = logging.StreamHandler()
        handler.setFormatter(logging.Formatter('see this %(asctime)s,%(msecs)03d - %(message)s', datefmt='%H:%M:%S'))
        logger.addHandler(handler)
    logger.setLevel(logging.WARNING)

    server = NodeServer(
        node=local_node,
        remote_nodes=remote_clients,
        cluster_configuration=ClusterConfiguration(
            election_timeout=ElectionTimeout(
                max_timeout=timedelta(seconds=4),
                min_timeout=timedelta(seconds=3)
            ),
            heartbeat_period=timedelta(seconds=1),
        )
    )
    await server.run(port)
    await asyncio.sleep(math.inf)


if __name__ == '__main__':
    asyncio.run(main())
