import asyncio
import unittest
from datetime import timedelta

from main import Cluster, NoLeaderInCluster, Node, Subject, Leader, TooManyLeaders, Candidate


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

    async def test_down_means_not_a_leader(self) -> None:
        the_node = Node(initial_role=Leader())
        cluster = Cluster({the_node})

        await the_node.take_down()

        assert cluster.take_me_to_a_leader() == NoLeaderInCluster()

    async def test_down_then_back_up_means_leader_back(self) -> None:
        the_node = Node(initial_role=Leader())
        cluster = Cluster({the_node})

        await the_node.take_down()
        await the_node.bring_back_up()

        assert cluster.take_me_to_a_leader() == the_node

    async def test_resurrected_subjects_are_subjects(self) -> None:
        the_node = Node(initial_role=Subject())
        cluster = Cluster({the_node})

        await the_node.take_down()
        await the_node.bring_back_up()

        assert cluster.take_me_to_a_leader() == NoLeaderInCluster()

    async def test_down_is_idempotent(self) -> None:
        the_node = Node(initial_role=Leader())
        cluster = Cluster({the_node})

        await the_node.take_down()
        await the_node.take_down()
        await the_node.bring_back_up()

        assert cluster.take_me_to_a_leader() == the_node

    async def test_up_is_idempotent(self) -> None:
        the_node = Node(initial_role=Leader())
        cluster = Cluster({the_node})

        await the_node.take_down()
        await the_node.bring_back_up()
        await the_node.bring_back_up()

        assert cluster.take_me_to_a_leader() == the_node

    async def test_non_leader_nodes_announce_candidacy_after_election_timeout_passes(self) -> None:
        the_node = Node(initial_role=Subject())
        cluster = Cluster(
            nodes={the_node},
            election_timeout=timedelta(seconds=0.1),
        )
        asyncio.create_task(cluster.run())

        await asyncio.sleep(0.2)

        assert the_node.role == Candidate()
