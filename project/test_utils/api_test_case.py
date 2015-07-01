import unittest


class ApiTestCase(unittest.TestCase):

    def assertInList(self, member, container, msg=None):
        """Modeled after TestCase.assertIn(), but testing for equality, not identity."""
        for item in container:
            if member == item:
                return
        standardMsg = "{} not found in list".format(member, container)
        self.fail(self._formatMessage(msg, standardMsg))

    def assertNotInList(self, member, container, msg=None):
        """Reverse to assertInList"""
        for item in container:
            if member == item:
                standardMsg = "{} found in list".format(member, container)
                self.fail(self._formatMessage(msg, standardMsg))