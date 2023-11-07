import unittest

from tests.fixtures import get_cluster, create_leader_node


class TestMessaging(unittest.IsolatedAsyncioTestCase):
    async def test_that_no_messages_sent_means_no_messages_returned(self) -> None:
        nodes = {create_leader_node()}
        cluster = await get_cluster(nodes)

        self.assertTupleEqual(await cluster.get_messages(), tuple())

    async def test_one_message_gets_returned(self) -> None:
        nodes = {create_leader_node()}
        cluster = await get_cluster(nodes)

        await cluster.send_message('Milkshake')

        self.assertTupleEqual(await cluster.get_messages(), ('Milkshake',))
