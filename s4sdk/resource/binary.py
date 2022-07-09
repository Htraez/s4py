from s4sdk.resource.abc import Resource


class BinaryResource(Resource):
    def __init__(self):
        super().__init__()

    @classmethod
    def read(cls, path: str):
        pass

    @property
    def content(self) -> bytes:
        pass

    def write(self, path: str):
        pass

