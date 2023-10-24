import unittest

from main import Cluster, NoLeaderInCluster, Node, Subject, Leader, TooManyLeaders


class TestCluster(unittest.IsolatedAsyncioTestCase):
    async def test_empty_clusters_have_no_leader(self) -> None:
        cluster = Cluster(set())

        assert cluster.take_me_to_a_leader() == NoLeaderInCluster()

    async def test_one_node_one_leader(self) -> None:
        the_node = Node()
        cluster = Cluster({the_node})

        assert cluster.take_me_to_a_leader() == the_node

    async def test_two_nodes_one_leader(self) -> None:
        leader = Node(initial_role=Leader())
        follower = Node(initial_role=Subject())
        cluster = Cluster({leader, follower})

        assert cluster.take_me_to_a_leader() == leader

    async def test_two_nodes_multiple_leaders(self) -> None:
        leader = Node(initial_role=Leader())
        follower = Node(initial_role=Leader())
        cluster = Cluster({leader, follower})

        with self.assertRaises(TooManyLeaders):
            assert cluster.take_me_to_a_leader()
