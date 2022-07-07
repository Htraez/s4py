from . import utils
from dataclasses import dataclass
from collections import defaultdict
import pandas as pd


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


class StringTable:
    def __init__(self, meta_data: StringTableMetadata = None, content: pd.DataFrame = None, bstr: bytes = None):
        if bstr is not None:
            b_pack = utils.BinPacker(bstr)
            self.meta_data = StringTableMetadata.from_binary_pack(b_pack)
            self.content = self._unpack_content(b_pack)
        elif meta_data is not None and content is not None:
            self.meta_data = meta_data
            self.content = content
        else:
            raise ValueError()

    @classmethod
    def from_stbl(cls, stbl_path: str):
        return cls(bstr=open(stbl_path, "rb").read())

    @classmethod
    def from_csv(cls, path: str):
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
        return cls(
            meta_data=StringTableMetadata.from_empty(num_entries=num_entries, str_length=str_len),
            content=content
        )

    def as_csv(self, path: str):
        self.content.to_csv(path, index=False)

    def as_stbl(self, path: str):
        b_pack = utils.BinPacker(bstr=b'', mode='w')
        self._repack_metadata(b_pack=b_pack)
        self._repack_content(b_pack=b_pack)
        with open(path, "wb") as file:
            file.write(b_pack.raw.getbuffer())
        b_pack.close()

    def _repack_metadata(self, b_pack: utils.BinPacker):
        b_pack.put_raw_bytes(self.meta_data.magic)
        b_pack.put_uint16(self.meta_data.version)
        b_pack.put_uint8(self.meta_data.compressed)
        b_pack.put_uint64(self.meta_data.num_entries)
        b_pack.off += 2
        b_pack.put_uint32(self.meta_data.str_length)

    def _repack_content(self, b_pack: utils.BinPacker):
        contents = self.content.to_dict(orient="index")
        for row, content in contents.items():
            b_pack.put_uint32(content.get("key_hash"))
            b_pack.put_uint8(content.get("flags"))
            b_pack.put_uint16(content.get("length"))
            val = content.get("val")
            b_pack.put_raw_bytes("".encode("utf-8") if val != val else val.encode("utf-8"))

    def _unpack_content(self, readable_pack: utils.BinPacker) -> pd.DataFrame:
        content = defaultdict(dict)
        for row in range(self.meta_data.num_entries):
            key_hash = readable_pack.get_uint32()
            flags = readable_pack.get_uint8() # What is in this? It's always 0.
            length = readable_pack.get_uint16()
            val = readable_pack.get_raw_bytes(length).decode('utf-8')
            content["key_hash"][row] = key_hash
            content["flags"][row] = flags
            content["length"][row] = length
            content["val"][row] = val
        return pd.DataFrame.from_dict(content)


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
    mnStringLength = f.get_uint32() # This is the total size of all
                                    # the strings plus one null byte
                                    # per string (to make the parsing
                                    # code faster, probably)

    entries = {}
    size = 0
    for _ in range(numEntries):
        keyHash = f.get_uint32()
        flags = f.get_uint8() # What is in this? It's always 0.
        length = f.get_uint16()
        val = f.get_raw_bytes(length).decode('utf-8')
        yield keyHash, val
