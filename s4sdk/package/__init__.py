# Provides useful tools for working with packages, including metapackage support
import os.path

from s4sdk import utils
from s4sdk.package.metapackage import MetaPackage
from s4sdk.package.dbpf import DbpfPackage
from s4sdk.package.dirpackage import DirPackage
from s4sdk import metadata
from s4sdk.resource.abc import Resource
from s4sdk.resource import Resource as _Resource, ResourceID, ResourceFilter
from s4sdk.resource.stbl import StringTable, StringTableMetadata
from s4sdk.resource.binary import BinaryResource
import pandas as pd
from typing import List


def open_package(filename, mode="r"):
    absname = os.path.abspath(filename)
    if mode == "r":
        if not os.path.exists(filename):
            raise FileNotFoundError(
                "No such file or directory: %s" % (filename,))
        if os.path.isdir(filename):
            return DirPackage(absname)
        with open(filename, "rb") as f:
            magic = f.read(4)
            if magic == b"DBPF":
                return DbpfPackage(filename)
        if filename.lower().endswith(".meta"):
            # It's a metapackage...
            try:
                return MetaPackage.open(filename)
            except UnicodeError:
                raise utils.FormatException("Invalid unicode in metapackage")
        raise utils.FormatException("Couldn't identify package format")
    elif mode == 'w':
        if filename.endswith(".package"):
            return DbpfPackage(filename, "w")
        elif filename.endswith("/") or os.path.isdir(filename):
            return DirPackage(filename, mode="w")


class Package:
    def __init__(self, dbfile):
        self.dbfile = dbfile
        child_generator = self.dbfile.scan_index()
        self.instances = [instance for instance in child_generator]

    @classmethod
    def from_package(cls, path: str):
        return cls(dbfile=open_package(path, mode="r"))

    @classmethod
    def create_empty(cls, path: str):
        if os.path.exists(path):
            raise ValueError(f"Package file at {path} already exist")
        return cls(dbfile=open_package(path, mode="w"))

    def list(self):
        return pd.DataFrame.from_dict({
            idx: {
                "type": instance.type,
                "group": instance.group,
                "instance_id": instance.instance,
                "resource_key": instance
            }
            for idx, instance in enumerate(self.instances)
        }, orient="index")

    def get(self, instance_id: int | List[int]) -> Resource:
        if not isinstance(instance_id, list):
            instance_id = [instance_id]
        for instance in self.instances:
            if instance.instance in instance_id:
                instance_id.remove(instance.instance)
                _resource = self.dbfile[instance]
                if _resource.id.type == metadata.ResourceType.STBL.value:
                    return StringTable.read_bytes(bstr=_resource.content)
                else:
                    return BinaryResource(
                        type=metadata.classify_type(instance.type),
                        group=instance.group,
                        instance=instance.instance,
                        content=_resource.content
                    )
        if instance_id:
            raise ValueError(f"Cannot find these instance in the package: {instance_id}")

    def insert(self, resource: Resource | List[Resource]):
        if not isinstance(resource, list):
            resource = [resource]
        for rsrc in resource:
            self.dbfile.put(rid=rsrc.rid, content=rsrc.content)
            self.dbfile.commit()

    def remove(self, instance_id: int | List[int]):
        if not isinstance(instance_id, list):
            instance_id = [instance_id]
        pass

    def export(self, instance_id: int, path: str):
        res = self.get(instance_id=instance_id)
        res.write(path)
