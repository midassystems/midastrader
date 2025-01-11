from abc import ABC, abstractmethod


class SystemEvent(ABC):
    def __init__(self):
        pass

    @abstractmethod
    def __str__(self) -> str:
        pass
