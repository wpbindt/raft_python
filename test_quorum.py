import unittest

from main import Cluster, NoLeader


class TestCluster(unittest.IsolatedAsyncioTestCase):
    async def test_empty_clusters_have_no_leader(self) -> None:
        cluster = Cluster(set())

        assert cluster.take_me_to_a_leader() == NoLeader()