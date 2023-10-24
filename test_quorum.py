import unittest

from main import Cluster, NoLeader, Node


class TestCluster(unittest.IsolatedAsyncioTestCase):
    async def test_empty_clusters_have_no_leader(self) -> None:
        cluster = Cluster(set())

        assert cluster.take_me_to_a_leader() == NoLeader()

    async def test_one_node_one_leader(self) -> None:
        the_node = Node()
        cluster = Cluster({the_node})

        assert cluster.take_me_to_a_leader() == the_node
