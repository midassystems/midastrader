from enum import Enum, auto
from abc import ABC, abstractmethod


class EventType(Enum):
    """
    Represents the types of events observed within the trading system.

    Categories:
        - Market Events: Events related to market data and order book updates.
        - Order Events: Events triggered by changes in orders and trades.
        - Portfolio Events: Events related to position, account, and equity updates.
        - Risk and End-of-Day Events: Events triggered by risk updates or end-of-day processing.
    """

    MARKET_DATA = auto()
    ORDER_BOOK = auto()
    SIGNAL = auto()
    ORDER_CREATED = auto()
    TRADE_EXECUTED = auto()
    EOD_EVENT = auto()
    # OLD
    POSITION_UPDATE = auto()
    ORDER_UPDATE = auto()
    ACCOUNT_UPDATE = auto()
    EQUITY_VALUE_UPDATE = auto()
    RISK_UPDATE = auto()
    TRADE_UPDATE = auto()
    TRADE_COMMISSION_UPDATE = auto()


class Subject:
    """
    Represents a subject in the Observer pattern that can notify observers of events.

    The `Subject` maintains a list of observers subscribed to specific event types.
    Observers are notified when the corresponding event occurs, enabling decoupled communication.
    """

    def __init__(self):
        """
        Initializes the Subject with an empty dictionary of observers.

        Each key in the dictionary corresponds to an `EventType`,
        and its value is a list of observers subscribed to that event.
        """
        self._observers = {}

    def attach(self, observer: "Observer", event_type: EventType) -> None:
        """
        Attaches an observer to a specific event type.

        Args:
            observer (Observer): The observer to attach.
            event_type (EventType): The event type the observer wants to subscribe to.
        """
        if event_type not in self._observers:
            self._observers[event_type] = []
        self._observers[event_type].append(observer)

    def detach(self, observer: "Observer", event_type: EventType) -> None:
        """
        Detaches an observer from a specific event type.

        Args:
            observer (Observer): The observer to detach.
            event_type (EventType): The event type the observer wants to unsubscribe from.
        """
        if (
            event_type in self._observers
            and observer in self._observers[event_type]
        ):
            self._observers[event_type].remove(observer)

    def notify(self, event_type: EventType, *args, **kwargs) -> None:
        """
        Notifies all observers subscribed to a specific event type.

        Behavior:
            - Iterates through all observers subscribed to the given `event_type`.
            - Calls the `handle_event` method of each observer, passing along the event data.

        Args:
            event_type (EventType): The event type that has occurred.
            *args: Additional positional arguments to be passed to the observers.
            **kwargs: Additional keyword arguments to be passed to the observers.

        """
        if event_type in self._observers:
            for observer in self._observers[event_type]:
                observer.handle_event(self, event_type, *args, **kwargs)


class Observer(ABC):
    """
    Abstract base class for observers in the Observer pattern.

    Observers are entities that subscribe to specific events emitted by a `Subject`.
    When an event occurs, the subject notifies its observers, and each observer handles the event.
    """

    @abstractmethod
    def handle_event(
        self,
        subject: Subject,
        event_type: EventType,
        *args,
        **kwargs,
    ):
        """
        Handles an event triggered by a `Subject`.

        Behavior:
            - This method must be implemented by all concrete subclasses.
            - Defines how the observer processes specific event types.

        Args:
            subject (Subject): The subject that triggered the event.
            event_type (EventType): The type of event that was triggered.
            *args: Additional positional arguments with event-specific data.
            **kwargs: Additional keyword arguments with event-specific data.

        """
        pass
