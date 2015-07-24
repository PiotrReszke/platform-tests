import functools

from test_utils import get_config_value


__all__ = ["Space"]


@functools.total_ordering
class Space(object):

    def __init__(self, name, guid):
        self.name = name
        self.guid = guid

    def __repr__(self):
        return "{0} (name={1}, guid={2})".format(self.__class__.__name__, self.name, self.guid)

    def __eq__(self, other):
        return self.name == other.name and self.guid == other.guid

    def __lt__(self, other):
        return self.guid < other.guid

    @classmethod
    def get_seedspace(cls):
        return cls(name="seedspace", guid=get_config_value("seedspace_guid"))