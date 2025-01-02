import unittest
from unittest.mock import Mock
from mbn import OhlcvMsg, BboMsg, BidAskPair, Side
from decimal import Decimal

from midas.message_bus import MessageBus, EventType
from midas.data.adaptors.ib.wrapper import DataApp


class TestDataApp(unittest.TestCase):
    def setUp(self):
        self.bus = MessageBus()
        self.data_app = DataApp(self.bus, tick_interval=5)

    def test_200_error_valid(self):
        # Simulate an error code for contract not found
        # Test
        self.data_app.error(
            reqId=-1,
            errorCode=200,
            errorString="Contract not found",
        )

        # Validate
        self.assertFalse(
            self.data_app.is_valid_contract
        )  # Verify is_valid_contract is set to False
        self.assertTrue(
            self.data_app.validate_contract_event.is_set()
        )  # Verify validate_contract_event is set

    def test_connectAck_valid(self):
        # Test
        self.data_app.connectAck()

        # Validate
        self.assertFalse(
            self.data_app.is_valid_contract
        )  # Verify is_valid_contract is set to False
        self.assertTrue(
            self.data_app.connected_event.is_set()
        )  # Verify validate_contract_event is set

    def test_nextvalidId_valid(self):
        id = 10

        # Test
        self.data_app.nextValidId(id)

        # Validate
        self.assertEqual(self.data_app.next_valid_order_id, id)
        self.assertTrue(self.data_app.valid_id_event.is_set())

    def test_contractDetails(self):
        # Test
        self.data_app.contractDetails(10, None)

        # Validate
        self.assertTrue(self.data_app.is_valid_contract)

    def test_contractDetailsEnd_valid(self):
        # Test
        self.data_app.contractDetailsEnd(10)

        # Validate
        self.assertTrue(self.data_app.validate_contract_event.is_set())

    def test_realtimeBar(self):
        # Mock ticker mapping to reqID
        self.data_app.reqId_to_instrument[123] = 2

        # Mock api response
        reqId = 123
        time = 165500000
        open_ = 109.9
        high = 110
        low = 105.6
        close = 108
        volume = 10000
        wap = 109
        count = 10

        # Test
        self.bus.publish = Mock()
        self.data_app.realtimeBar(
            reqId,
            time,
            open_,
            high,
            low,
            close,
            volume,
            wap,
            count,
        )

        # Validate
        args = self.bus.publish.call_args[0]
        self.assertEqual(args[0], EventType.DATA)
        self.assertIsInstance(args[1], OhlcvMsg)

    def test_tickPrice(self):
        bbo_obj = BboMsg(
            instrument_id=1,
            ts_event=0,
            price=0,
            size=0,
            side=Side.NONE,
            flags=0,
            ts_recv=0,
            sequence=0,
            levels=[
                BidAskPair(
                    bid_px=0,
                    ask_px=0,
                    bid_sz=0,
                    ask_sz=0,
                    bid_ct=0,
                    ask_ct=0,
                )
            ],
        )
        self.data_app.tick_data[123] = bbo_obj

        bbo_obj.levels[0].bid_px = 12345432

        # Mock api response
        reqId = 123
        tickTypeBid = 1
        tickTypeAsk = 2
        tickTypeLast = 4
        price = 109.9
        attrib = Mock()

        # Test
        self.bus.publish = Mock()
        self.data_app.tickPrice(reqId, tickTypeBid, price, attrib)
        self.assertEqual(
            self.data_app.tick_data[123].levels[0].bid_px, int(price * 1e9)
        )

        self.data_app.tickPrice(reqId, tickTypeAsk, price, attrib)
        self.assertEqual(
            self.data_app.tick_data[123].levels[0].ask_px, int(price * 1e9)
        )

        self.data_app.tickPrice(reqId, tickTypeLast, price, attrib)
        self.assertEqual(self.data_app.tick_data[123].price, int(price * 1e9))

    def test_tickSize(self):

        bbo_obj = BboMsg(
            instrument_id=1,
            ts_event=0,
            price=0,
            size=0,
            side=Side.NONE,
            flags=0,
            ts_recv=0,
            sequence=0,
            levels=[
                BidAskPair(
                    bid_px=0,
                    ask_px=0,
                    bid_sz=0,
                    ask_sz=0,
                    bid_ct=0,
                    ask_ct=0,
                )
            ],
        )
        self.data_app.tick_data[123] = bbo_obj

        bbo_obj.levels[0].bid_px = 12345432

        # Mock api response
        reqId = 123
        tickTypeBid = 0
        tickTypeAsk = 3
        tickTypeLast = 5
        size = Decimal(3455)

        # Test
        self.bus.publish = Mock()
        self.data_app.tickSize(reqId, tickTypeBid, size)
        self.assertEqual(
            self.data_app.tick_data[123].levels[0].bid_sz, int(size)
        )

        self.data_app.tickSize(reqId, tickTypeAsk, size)
        self.assertEqual(
            self.data_app.tick_data[123].levels[0].ask_sz, int(size)
        )

        self.data_app.tickSize(reqId, tickTypeLast, size)
        self.assertEqual(self.data_app.tick_data[123].size, int(size))

    def test_tickString(self):
        bbo_obj = BboMsg(
            instrument_id=1,
            ts_event=0,
            price=0,
            size=0,
            side=Side.NONE,
            flags=0,
            ts_recv=0,
            sequence=0,
            levels=[
                BidAskPair(
                    bid_px=0,
                    ask_px=0,
                    bid_sz=0,
                    ask_sz=0,
                    bid_ct=0,
                    ask_ct=0,
                )
            ],
        )
        self.data_app.tick_data[123] = bbo_obj

        # Mock api response
        reqId = 123
        tickType = 45
        value = "123456"

        # Test
        self.data_app.tickString(reqId, tickType, value)
        self.assertEqual(
            self.data_app.tick_data[123].hd.ts_event, int(int(value) * 1e9)
        )

    def test_push_market_event(self):
        bbo_obj = BboMsg(
            instrument_id=1,
            ts_event=0,
            price=0,
            size=0,
            side=Side.NONE,
            flags=0,
            ts_recv=0,
            sequence=0,
            levels=[
                BidAskPair(
                    bid_px=0,
                    ask_px=0,
                    bid_sz=0,
                    ask_sz=0,
                    bid_ct=0,
                    ask_ct=0,
                )
            ],
        )
        self.data_app.tick_data[123] = bbo_obj
        self.data_app.tick_data[321] = bbo_obj

        # Test
        self.bus.publish = Mock()
        self.data_app.push_market_event()

        # Validate
        self.assertEqual(self.bus.publish.call_count, 2)

        # Access all calls made to publish
        calls = self.bus.publish.call_args_list

        # Validate the first call
        first_call_args = calls[0][0]
        self.assertEqual(first_call_args[0], EventType.DATA)
        self.assertEqual(first_call_args[1], bbo_obj)

        # Validate the second call
        second_call_args = calls[1][0]
        self.assertEqual(second_call_args[0], EventType.DATA)
        self.assertEqual(second_call_args[1], bbo_obj)


if __name__ == "__main__":
    unittest.main()
