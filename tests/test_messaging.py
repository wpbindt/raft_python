import unittest

from tests.fixtures import get_running_cluster, create_leader_node


class TestMessaging(unittest.IsolatedAsyncioTestCase):
    async def test_that_no_messages_sent_means_no_messages_returned(self) -> None:
        cluster = await get_running_cluster({create_leader_node()})

        self.assertTupleEqual(await cluster.get_messages(), tuple())

    async def test_one_message_gets_returned(self) -> None:
        cluster = await get_running_cluster({create_leader_node()})

        await cluster.send_message('Milkshake')

        self.assertTupleEqual(await cluster.get_messages(), ('Milkshake',))

    async def test_down_nodes_do_not_take_messages(self) -> None:
        node = create_leader_node()
        cluster = await get_running_cluster({node})
        await node.take_down()

        await cluster.send_message('Milkshake')

        self.assertTupleEqual(await cluster.get_messages(), tuple())
