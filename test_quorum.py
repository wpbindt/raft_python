from __future__ import annotations

import asyncio
import unittest
from datetime import timedelta
from itertools import cycle

from main import Cluster, NoLeaderInCluster, Node, Subject, Leader, TooManyLeaders, Candidate, ElectionTimeout, \
    ClusterConfiguration


class TestCluster(unittest.IsolatedAsyncioTestCase):
    def get_cluster(
        self,
        nodes: set[Node],
        election_timeout: ElectionTimeout = ElectionTimeout(timedelta(days=1)),
        heartbeat_period: timedelta = timedelta(days=1),
    ) -> Cluster:
        return Cluster(
            nodes=nodes,
            cluster_configuration=ClusterConfiguration(
                election_timeout=election_timeout,
                heartbeat_period=heartbeat_period,
            ),
        )

    async def test_empty_clusters_have_no_leader(self) -> None:
        cluster = self.get_cluster(nodes=set())

        assert cluster.take_me_to_a_leader() == NoLeaderInCluster()

    async def test_one_node_one_leader(self) -> None:
        the_node = Node()
        cluster = self.get_cluster({the_node})

        assert cluster.take_me_to_a_leader() == the_node

    async def test_two_nodes_one_leader(self) -> None:
        leader = Node(initial_role=Leader())
        follower = Node(initial_role=Subject())
        cluster = self.get_cluster({leader, follower})

        assert cluster.take_me_to_a_leader() == leader

    async def test_two_nodes_multiple_leaders(self) -> None:
        leader = Node(initial_role=Leader())
        follower = Node(initial_role=Leader())
        cluster = self.get_cluster({leader, follower})

        with self.assertRaises(TooManyLeaders):
            assert cluster.take_me_to_a_leader()

    async def test_down_means_not_a_leader(self) -> None:
        the_node = Node(initial_role=Leader())
        cluster = self.get_cluster({the_node})

        await the_node.take_down()

        assert cluster.take_me_to_a_leader() == NoLeaderInCluster()

    async def test_down_then_back_up_means_leader_back(self) -> None:
        the_node = Node(initial_role=Leader())
        cluster = self.get_cluster({the_node})

        await the_node.take_down()
        await the_node.bring_back_up()

        assert cluster.take_me_to_a_leader() == the_node

    async def test_resurrected_subjects_are_subjects(self) -> None:
        the_node = Node(initial_role=Subject())
        cluster = self.get_cluster({the_node})

        await the_node.take_down()
        await the_node.bring_back_up()

        assert cluster.take_me_to_a_leader() == NoLeaderInCluster()

    async def test_down_is_idempotent(self) -> None:
        the_node = Node(initial_role=Leader())
        cluster = self.get_cluster({the_node})

        await the_node.take_down()
        await the_node.take_down()
        await the_node.bring_back_up()

        assert cluster.take_me_to_a_leader() == the_node, str(cluster.take_me_to_a_leader())

    async def test_up_is_idempotent(self) -> None:
        the_node = Node(initial_role=Leader())
        cluster = self.get_cluster({the_node})

        await the_node.take_down()
        await the_node.bring_back_up()
        await the_node.bring_back_up()

        assert cluster.take_me_to_a_leader() == the_node

    async def test_non_leader_nodes_announce_candidacy_after_election_timeout_passes(self) -> None:
        the_node = Node(initial_role=Subject())
        cluster = self.get_cluster(
            nodes={the_node},
            election_timeout=ElectionTimeout(timedelta(seconds=0.02)),
        )
        asyncio.create_task(cluster.run())

        await asyncio.sleep(0.05)

        assert the_node.role == Candidate()

    async def test_leader_nodes_do_not_become_candidates(self) -> None:
        the_node = Node(initial_role=Leader())
        cluster = self.get_cluster(
            nodes={the_node},
            election_timeout=ElectionTimeout(timedelta(seconds=0.02)),
        )
        asyncio.create_task(cluster.run())

        await asyncio.sleep(0.05)

        assert cluster.take_me_to_a_leader() == the_node

    async def test_candidacy_is_announced_in_random_way(self) -> None:
        the_node = Node(initial_role=Subject())
        cluster = self.get_cluster(
            nodes={the_node},
            election_timeout=ElectionTimeout(
                max_timeout=timedelta(seconds=0.2),
                randomization=(cycle((0.1,)))
            ),
        )
        asyncio.create_task(cluster.run())

        await asyncio.sleep(0.03)

        assert the_node.role == Candidate()

    async def test_candidacy_is_not_announced_before_min_timeout(self) -> None:
        the_node = Node(initial_role=Subject())
        cluster = self.get_cluster(
            nodes={the_node},
            election_timeout=ElectionTimeout(
                max_timeout=timedelta(seconds=0.33),
                min_timeout=timedelta(seconds=0.33),
                randomization=(cycle((0.1,)))
            ),
        )
        asyncio.create_task(cluster.run())

        await asyncio.sleep(0.01)

        assert isinstance(the_node.role, Subject)

    async def test_live_leaders_prevent_elections(self) -> None:
        subject = Node(initial_role=Subject())
        leader = Node(initial_role=Leader())
        cluster = self.get_cluster(
            nodes={leader, subject},
            election_timeout=ElectionTimeout(max_timeout=timedelta(seconds=0.05), min_timeout=timedelta(seconds=0.05)),
            heartbeat_period=timedelta(seconds=0.01),
        )
        asyncio.create_task(cluster.run())

        await asyncio.sleep(0.1)

        assert subject.role != Candidate()

    async def test_down_leaders_do_not_prevent_elections(self) -> None:
        subject = Node(initial_role=Subject())
        leader = Node(initial_role=Leader())
        heartbeat = timedelta(seconds=0.03)
        candidacy_timeout = timedelta(seconds=0.05)
        cluster = self.get_cluster(
            nodes={leader, subject},
            election_timeout=ElectionTimeout(max_timeout=candidacy_timeout, min_timeout=candidacy_timeout),
            heartbeat_period=timedelta(seconds=0.05),
        )
        asyncio.create_task(cluster.run())
        await asyncio.sleep(0.5 * heartbeat.total_seconds())
        await leader.take_down()

        await asyncio.sleep(candidacy_timeout.total_seconds())

        assert subject.role == Candidate()

    async def test_leader_down_after_first_heartbeat_still_means_election(self) -> None:
        self.fail(
            'should be like the above, but I clearly dont '
            'understand the test suite as it is (or my implementations are faulty'
        )
