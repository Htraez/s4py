import pandas as pd

from s4sdk.resource.abc import Resource
from s4sdk import utils, metadata
from dataclasses import dataclass
from collections import defaultdict


@dataclass
class StringTableMetadata:
    magic: bytes
    version: int
    compressed: int
    num_entries: int
    str_length: int

    @classmethod
    def from_binary_pack(cls, b_pack: utils.BinPacker):
        magic = b_pack.get_raw_bytes(4)
        if magic != b'STBL':
            raise utils.FormatException("Bad magic")
        version = b_pack.get_uint16()
        if version != 5:
            raise utils.FormatException("We only support STBLv5")
        compressed = b_pack.get_int8()
        num_entries = b_pack.get_uint64()
        b_pack.off += 2
        str_length = b_pack.get_uint32()
        return cls(magic=magic, version=version, compressed=compressed, num_entries=num_entries, str_length=str_length)

    @classmethod
    def from_empty(cls, num_entries: int, str_length: int):
        return cls(magic=b'STBL', version=5, compressed=0, num_entries=num_entries, str_length=str_length)


class StringTable(Resource):
    def __init__(self, meta_data=None, entries=None):
        super().__init__(type=metadata.ResourceType.STBL)
        self.meta_data = meta_data or StringTableMetadata.from_empty(num_entries=0, str_length=0)
        self.entries: pd.DataFrame = entries if entries is not None else pd.DataFrame()

    @classmethod
    def read(cls, path: str):
        bstr = open(path, "rb").read()
        return StringTable.read_bytes(bstr=bstr)

    @classmethod
    def read_bytes(cls, bstr: bytes):
        b_pack = utils.BinPacker(bstr)
        meta_data = StringTableMetadata.from_binary_pack(b_pack=b_pack)

        content = defaultdict(dict)
        for row in range(meta_data.num_entries):
            key_hash = b_pack.get_uint32()
            flags = b_pack.get_uint8()
            length = b_pack.get_uint16()
            val = b_pack.get_raw_bytes(length).decode('utf-8')
            content["key_hash"][row] = key_hash
            content["flags"][row] = flags
            content["length"][row] = length
            content["val"][row] = val
        entries = pd.DataFrame.from_dict(content)
        return cls(meta_data=meta_data, entries=entries)

    @classmethod
    def read_csv(cls, path: str):
        content = pd.read_csv(path).to_dict()
        n = len(content["key_hash"])
        total_len = 0
        str_len = 0
        for row in range(0, n):
            if content["val"][row] != content["val"][row]:
                new_len = 0
            else:
                new_len = len(content["val"][row].encode("utf-8"))
            content["length"][row] = new_len
            total_len += new_len
            str_len += len(content["val"][row]) if new_len else new_len

        num_entries = n
        str_len = total_len + num_entries

        meta_data = StringTableMetadata.from_empty(num_entries=num_entries, str_length=str_len)
        entries = content
        return cls(meta_data=meta_data, entries=entries)

    def write(self, path: str):
        b_pack = self.pack_bytes()
        with open(path, "wb") as file:
            file.write(b_pack.raw.getbuffer())
        b_pack.close()

    def write_csv(self, path: str):
        self.entries.to_csv(path, index=False)

    @property
    def content(self) -> bytes:
        return self.pack_bytes().raw

    def pack_bytes(self) -> utils.BinPacker:
        b_pack = utils.BinPacker(bstr=b'', mode='w')
        self._repack_metadata(b_pack=b_pack)
        self._repack_content(b_pack=b_pack)
        return b_pack

    def _repack_metadata(self, b_pack: utils.BinPacker):
        b_pack.put_raw_bytes(self.meta_data.magic)
        b_pack.put_uint16(self.meta_data.version)
        b_pack.put_uint8(self.meta_data.compressed)
        b_pack.put_uint64(self.meta_data.num_entries)
        b_pack.off += 2
        b_pack.put_uint32(self.meta_data.str_length)

    def _repack_content(self, b_pack: utils.BinPacker):
        contents = self.entries.to_dict(orient="index")
        for row, content in contents.items():
            b_pack.put_uint32(content.get("key_hash"))
            b_pack.put_uint8(content.get("flags"))
            b_pack.put_uint16(content.get("length"))
            val = content.get("val")
            b_pack.put_raw_bytes("".encode("utf-8") if val != val else val.encode("utf-8"))


def read_stbl(bstr):
    """Parse a string table (ID 0x220557DA)"""
    f = utils.BinPacker(bstr)
    if f.get_raw_bytes(4) != b'STBL':
        raise utils.FormatException("Bad magic")
    version = f.get_uint16()
    if version != 5:
        raise utils.FormatException("We only support STBLv5")
    compressed = f.get_uint8()
    numEntries = f.get_uint64()
    f.off += 2
    mnStringLength = f.get_uint32()
    # This is the total size of all the strings plus one null byte per string (to make the parsing code faster, probably)

    entries = {}
    size = 0
    for _ in range(numEntries):
        keyHash = f.get_uint32()
        flags = f.get_uint8() # What is in this? It's always 0.
        length = f.get_uint16()
        val = f.get_raw_bytes(length).decode('utf-8')
        yield keyHash, val
