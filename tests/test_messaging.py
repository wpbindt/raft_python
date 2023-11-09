import unittest

from tests.fixtures import get_running_cluster, create_leader_node, get_frozen_cluster, create_candidate_node, \
    create_subject_node


class TestMessaging(unittest.IsolatedAsyncioTestCase):
    async def test_that_no_messages_sent_means_no_messages_returned(self) -> None:
        cluster = await get_running_cluster({create_leader_node()})

        self.assertTupleEqual(await cluster.get_messages(), tuple())

    async def test_one_message_gets_returned(self) -> None:
        cluster = await get_running_cluster({create_leader_node()})

        await cluster.send_message('Milkshake')

        self.assertTupleEqual(await cluster.get_messages(), ('Milkshake',))

    async def test_non_leader_nodes_do_not_take_messages(self) -> None:
        down_node = create_leader_node()
        await down_node.take_down()
        for node in {create_subject_node(), create_candidate_node(), down_node}:
            with self.subTest(node.role.__class__.__name__):
                cluster = get_frozen_cluster({node})

                await cluster.send_message('Milkshake')

                self.assertTupleEqual(await cluster.get_messages(), tuple())
