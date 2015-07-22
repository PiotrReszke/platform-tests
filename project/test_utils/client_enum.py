from enum import Enum


__all__ = ["Role"]


class Role(Enum):
    undefined = "undefined"
    admin = "admin"
    org_manager = ("managers",)

