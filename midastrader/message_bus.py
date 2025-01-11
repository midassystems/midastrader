import queue
import threading
from enum import Enum, auto


class EventType(Enum):
    """
    Represents the types of events observed within the trading system.

    Categories:
        - Market Events: Events related to market data and order book updates.
        - Order Events: Events triggered by changes in orders and trades.
        - Portfolio Events: Events related to position, account, and equity updates.
        - Risk and End-of-Day Events: Events triggered by risk updates or end-of-day processing.
    """

    # Events
    DATA = auto()
    ORDER_BOOK = auto()
    SIGNAL = auto()
    ORDER = auto()
    TRADE = auto()

    # Update Events
    SIGNAL_UPDATE = auto()
    POSITION_UPDATE = auto()
    ORDER_UPDATE = auto()
    ACCOUNT_UPDATE = auto()
    ACCOUNT_UPDATE_LOG = auto()
    EQUITY_UPDATE = auto()
    TRADE_UPDATE = auto()
    TRADE_COMMISSION_UPDATE = auto()
    RISK_UPDATE = auto()

    # Flags
    UPDATE_EQUITY = auto()
    UPDATE_SYSTEM = auto()

    ORDER_BOOK_UPDATED = auto()
    OB_PROCESSED = auto()
    EOD_PROCESSED = auto()
    DATA_PROCESSED = auto()
    EQUITY_UPDATED = auto()
    EOD = auto()


class MessageBus:
    def __init__(self):
        self.topics = {
            EventType.DATA: queue.Queue(),
            EventType.ORDER_BOOK: queue.Queue(),
            EventType.SIGNAL: queue.Queue(),
            EventType.ORDER: queue.Queue(),
            EventType.TRADE: queue.Queue(),
            EventType.TRADE_COMMISSION_UPDATE: queue.Queue(),
            EventType.SIGNAL_UPDATE: queue.Queue(),
            EventType.POSITION_UPDATE: queue.Queue(),
            EventType.ORDER_UPDATE: queue.Queue(),
            EventType.ACCOUNT_UPDATE: queue.Queue(),
            EventType.ACCOUNT_UPDATE_LOG: queue.Queue(),
            EventType.EQUITY_UPDATE: queue.Queue(),
            EventType.TRADE_UPDATE: queue.Queue(),
            EventType.ORDER_BOOK_UPDATED: False,
            EventType.OB_PROCESSED: False,
            EventType.EOD_PROCESSED: False,
            EventType.DATA_PROCESSED: False,
            EventType.EQUITY_UPDATED: False,
            EventType.EOD: False,
            EventType.UPDATE_EQUITY: False,
            EventType.UPDATE_SYSTEM: False,
        }

        self.lock = threading.Lock()

    def subscribe(self, topic: EventType):
        """
        Subscribe to a topic.
        For queue-based topics: Returns the queue itself.
        For flag-based topics: Returns the current flag value.
        """
        with self.lock:
            if topic not in self.topics:
                raise ValueError(f"Topic '{topic}' is not defined.")

            if isinstance(self.topics[topic], queue.Queue):
                return self.topics[topic]  # Return the queue
            else:
                return self.topics[topic]  # Return the current flag value

    def publish(self, topic: EventType, message: object) -> None:
        """
        Publish a message to a topic.
        For queue-based topics: Adds the message to the queue.
        For flag-based topics: Updates the shared flag value.
        """
        with self.lock:
            if topic not in self.topics:
                raise ValueError(f"Topic '{topic}' is not defined.")

            if isinstance(self.topics[topic], queue.Queue):
                # Queue-based topic
                self.topics[topic].put(message)
            else:
                # Flag-based topic
                self.topics[topic] = message

    def get_flag(self, topic: EventType) -> object:
        """
        Get the current value of a flag-based topic.
        """
        with self.lock:
            if topic not in self.topics or isinstance(
                self.topics[topic], queue.Queue
            ):
                raise ValueError(f"Topic '{topic}' is not a flag-based topic.")
            return self.topics[topic]
