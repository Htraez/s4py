from s4sdk.resource.abc import Resource
from s4sdk.metadata import ResourceType


class BinaryResource(Resource):
    def __init__(self, type: ResourceType, group: int, instance: int, content: bytes):
        super().__init__(type=type, group=group, instance=instance, content=content)

    @classmethod
    def read(cls, path: str, **kwargs):
        file = open(path, "rb")
        instance = cls(
            type=kwargs.get("type"),
            group=kwargs.get("group"),
            instance=kwargs.get("instance"),
            content=file.read()
        )
        return instance

    @property
    def content(self) -> bytes:
        return self._bstr

    def write(self, path: str):
        with open(path, "wb") as file:
            file.write(self._bstr)

