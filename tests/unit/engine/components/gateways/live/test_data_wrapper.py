import unittest
from unittest.mock import Mock, MagicMock
from midas.engine.components.observer.base import EventType
from midas.engine.components.gateways.live.data_client.wrapper import DataApp
from midas.utils.logger import SystemLogger
from mbn import OhlcvMsg, BboMsg, BidAskPair, Side


class TestDataApp(unittest.TestCase):
    def setUp(self):
        # Mock Logger
        self.logger = SystemLogger()
        self.logger.get_logger = MagicMock()

        self.data_app = DataApp(tick_interval=5)

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
        self.data_app.notify = Mock()
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
        args = self.data_app.notify.call_args[0]
        self.assertEqual(args[0], EventType.MARKET_DATA)
        self.assertIsInstance(args[1], OhlcvMsg)

    # TODO: Not passing
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
        self.data_app.tickPrice(reqId, tickTypeBid, price, attrib)
        self.assertEqual(
            self.data_app.tick_data[123].levels[0].bid_px, int(price * 1e9)
        )

        self.data_app.tickPrice(reqId, tickTypeAsk, price, attrib)
        self.assertEqual(self.data_app.tick_data[123].levels[0].ask_px, price)

        self.data_app.tickPrice(reqId, tickTypeLast, price, attrib)
        self.assertEqual(self.data_app.tick_data[123].price, price)

    def test_tickSize(self):
        pass

    def test_tickString(self):
        pass

    def test_push_market_event(self):
        pass


if __name__ == "__main__":
    unittest.main()
