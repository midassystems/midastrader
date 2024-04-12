from enum import Enum, auto
from abc import ABC, abstractmethod

class EventType(Enum):
    POSITION_UPDATE = auto()
    ORDER_UPDATE = auto()
    ACCOUNT_DETAIL_UPDATE = auto()
    MARKET_EVENT = auto()
    RISK_MODEL_UPDATE = auto()

class Observer(ABC):
    @abstractmethod
    def update(self, subject, event_type: EventType):
        pass

class Subject:
    def __init__(self):
        self._observers = {}  # Maps EventType to observers interested in that event

    def attach(self, observer: Observer, event_type: EventType):
        if event_type not in self._observers:
            self._observers[event_type] = []
        self._observers[event_type].append(observer)

    def detach(self, observer: Observer, event_type: EventType):
        if event_type in self._observers and observer in self._observers[event_type]:
            self._observers[event_type].remove(observer)

    def notify(self, event_type: EventType):
        if event_type in self._observers:
            for observer in self._observers[event_type]:
                observer.update(self, event_type)
