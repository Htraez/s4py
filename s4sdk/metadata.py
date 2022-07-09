from enum import Enum


class ResourceType(Enum):
    STBL: int = 53690476
    GFX: int = 1659684250
    DDS: int = 11720834
    SIM_DATA: int = 1415235194
    OBJ_TUNING: int = 3055412916


def classify_type(type: int):
    for type_str in ResourceType.__annotations__.keys():
        if ResourceType[type_str].value == type:
            return ResourceType[type_str]
    raise ValueError(f"Resource type '{type}' is unsupported")
