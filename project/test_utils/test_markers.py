#
# Copyright (c) 2016 Intel Corporation
#
# Licensed under the Apache License, Version 2.0 (the "License";
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#    http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
#

import inspect


__all__ = ["components", "priority", "PRIORITY_LEVELS", "DEFAULT_PRIORITY"]

PRIORITY_LEVELS = ("p0", "p1", "p2")
DEFAULT_PRIORITY = PRIORITY_LEVELS[0]


class PriorityDecorator(object):

    def __init__(self, priority_level):
        if priority_level not in PRIORITY_LEVELS:
            raise TypeError("{} not in allowed priorities {}".format(priority_level, PRIORITY_LEVELS))
        self.priority_level = priority_level

    def __call__(self, f):
        if not inspect.isfunction(f) and not f.__name__.startswith("test_"):
            raise TypeError("Priority decorator can only be used on a test method.")
        f.priority = self.priority_level
        return f


class PriorityGenerator(object):

    def __getattr__(self, priority_level):
        return PriorityDecorator(priority_level)


class ComponentDecorator(object):

    def __init__(self, *args):
        self.components = args

    def __call__(self, c):
        if not inspect.isclass(c):
            raise TypeError("Component decorator should be used on a class.")
        c.components = self.components
        return c


priority = PriorityGenerator()
components = ComponentDecorator
