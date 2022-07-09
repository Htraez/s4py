from s4sdk import metadata
from abc import ABC, abstractmethod
from s4sdk.resource import ResourceID


class Resource(ABC):
    def __init__(self):
        self._group = 0
        self._instance = None
        self._bstr = None
        self._type = None

    @classmethod
    @abstractmethod
    def read(cls, path: str):
        pass

    @property
    def rid(self) -> str:
        return ResourceID(group=self.group, instance=self.instance, type=self.type)

    @property
    def group(self) -> int:
        return self._group

    @property
    def instance(self) -> int:
        return self._instance

    @property
    def type(self) -> metadata.ResourceType:
        return self._type

    @property
    @abstractmethod
    def content(self) -> bytes:
        return self._bstr

    @abstractmethod
    def write(self, path: str):
        pass
