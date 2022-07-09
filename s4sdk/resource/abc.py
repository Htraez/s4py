from s4sdk import metadata
from abc import ABC, abstractmethod
from s4sdk.resource import ResourceID


class Resource(ABC):
    def __init__(self, type: metadata.ResourceType, content: bytes = None, group: int = 0, instance: int = None):
        self._group = group
        self._instance = instance
        self._bstr = content
        self._type = type.value

    @classmethod
    @abstractmethod
    def read(cls, path: str):
        pass

    @property
    def rid(self) -> ResourceID:
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
