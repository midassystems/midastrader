from enum import Enum, auto
from abc import ABC, abstractmethod

class EventType(Enum):
    """Enum for different types of events that can be observed."""
    POSITION_UPDATE = auto()
    ORDER_UPDATE = auto()
    ACCOUNT_DETAIL_UPDATE = auto()
    MARKET_EVENT = auto()
    RISK_MODEL_UPDATE = auto()

class Observer(ABC):
    """Abstract base class for observers that need to respond to subject events."""
    @abstractmethod
    def update(self, subject, event_type: EventType):
        """
        Update the observer based on an event.

        Parameters:
        - subject (Subject): The subject that triggered the event.
        - event_type (EventType): The type of event that was triggered.
        """
        pass

class Subject:
    """Class representing a subject that can notify observers about various events."""
    def __init__(self):
        """Initialize the Subject with an empty observer dictionary."""
        self._observers = {}  # Maps EventType to observers interested in that event

    def attach(self, observer: Observer, event_type: EventType):
        """
        Attach an observer to a specific event type.

        Parameters:
        - observer (Observer): The observer to attach.
        - event_type (EventType): The event type to which the observer should be attached.
        """
        if event_type not in self._observers:
            self._observers[event_type] = []
        self._observers[event_type].append(observer)

    def detach(self, observer: Observer, event_type: EventType):
        """
        Detach an observer from a specific event type.

        Parameters:
        - observer (Observer): The observer to detach.
        - event_type (EventType): The event type from which the observer should be detached.
        """
        if event_type in self._observers and observer in self._observers[event_type]:
            self._observers[event_type].remove(observer)

    def notify(self, event_type: EventType):
        """
        Notify all observers about an event.

        Parameters:
        - event_type (EventType): The event type that has occurred.
        """
        if event_type in self._observers:
            for observer in self._observers[event_type]:
                observer.update(self, event_type)
