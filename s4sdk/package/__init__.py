# Provides useful tools for working with packages, including metapackage support
import os.path

from s4sdk import utils
from s4sdk.package.metapackage import MetaPackage
from s4sdk.package.dbpf import DbpfPackage
from s4sdk.package.dirpackage import DirPackage
from s4sdk import metadata
from s4sdk.resource.abc import Resource
from s4sdk.resource import Resource as _Resource, ResourceID, ResourceFilter
import pandas as pd


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

    def get(self, instance_id: int) -> Resource:
        for instance in self.instances:
            if instance.instance == instance_id:
                _resource = self.dbfile[instance]
                #TODO: convert _Resource to Resource

    def insert(self, type: metadata.ResourceType, instance: int, resource: Resource):
        rid = ResourceID(group=0, instance=instance, type=type.value)
        self.dbfile.put(rid=rid, content=resource.content)
        self.dbfile.commit()

    def remove(self, instance_id: str):
        pass

    def export(self, instance_id: int, path: str):
        res = self.get(instance_id=instance_id)
        res.write(path)

    def repack(self, destination: str, file_name: str):
        pass
