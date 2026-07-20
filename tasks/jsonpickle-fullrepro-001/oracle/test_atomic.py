# This document is free and open-source software, subject to the OSI-approved
# BSD license below.
#
# Copyright (c) 2014 Alexis Petrounias <www.petrounias.org>,
# All rights reserved.
#
# Redistribution and use in source and binary forms, with or without
# modification, are permitted provided that the following conditions are met:
#
# * Redistributions of source code must retain the above copyright notice, this
# list of conditions and the following disclaimer.
#
# * Redistributions in binary form must reproduce the above copyright notice,
# this list of conditions and the following disclaimer in the documentation
# and/or other materials provided with the distribution.
#
# * Neither the name of the author nor the names of its contributors may be used
# to endorse or promote products derived from this software without specific
# prior written permission.
#
# THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS"
# AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE
# IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE
# DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT HOLDER OR CONTRIBUTORS BE LIABLE
# FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL
# DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR
# SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER
# CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY,
# OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE
# OF THIS SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.
"""
Unit tests for collections
"""

from collections import OrderedDict, defaultdict

import jsonpickle

__status__ = "Stable"
__version__ = "1.0.0"
__maintainer__ = "Alexis Petrounias <www.petrounias.org>"
__author__ = "Alexis Petrounias <www.petrounias.org>"


"""
Classes featuring various collections used by
:mod:`restorable_collections_tests` unit tests; these classes must be
module-level (including the default dictionary factory method) so that they
can be pickled.

Tests restorable collections by creating pickled structures featuring
no cycles, self cycles, and mutual cycles, for all supported dictionary and
set wrappers. Python built-in dictionaries and sets are also tested with
expectation of failure via raising exceptions.

"""


class Group:
    def __init__(self, name):
        super().__init__()
        self.name = name
        self.elements = []

    def __repr__(self):
        return f"Group({self.name})"


class C:
    def __init__(self, v):
        super().__init__()
        self.v = v
        self.plain = dict()
        self.plain_ordered = OrderedDict()
        self.plain_default = defaultdict(c_factory)

    def add(self, key, value):
        self.plain[key] = (key, value)
        self.plain_ordered[key] = (key, value)
        self.plain_default[key] = (key, value)

    def __hash__(self):
        return hash(self.v) if hasattr(self, "v") else id(self)

    def __repr__(self):
        return f"C({self.v})"


def c_factory():
    return (C(0), "_")


class D:
    def __init__(self, v):
        super().__init__()
        self.v = v
        self.plain = set()

    def add(self, item):
        self.plain.add(item)

    def __hash__(self):
        return hash(self.v) if hasattr(self, "v") else id(self)

    def __repr__(self):
        return f"D({self.v})"


def pickle_and_unpickle(obj):
    encoded = jsonpickle.encode(obj, keys=True)
    return jsonpickle.decode(encoded, keys=True)


def test_dict_no_cycle():
    g = Group("group")
    c1 = C(42)
    g.elements.append(c1)
    c2 = C(67)
    g.elements.append(c2)
    c1.add(c2, "a")  # points to c2, which does not point to anything

    assert c2 in c1.plain
    assert c2 in c1.plain_ordered
    assert c2 in c1.plain_default

    gu = pickle_and_unpickle(g)
    c1u = gu.elements[0]
    c2u = gu.elements[1]

    # check existence of keys directly
    assert c2u in c1u.plain.keys()
    assert c2u in c1u.plain_ordered.keys()
    assert c2u in c1u.plain_default.keys()

    # check direct key-based lookup
    assert c2u == c1u.plain[c2u][0]
    assert c2u == c1u.plain_ordered[c2u][0]
    assert c2u == c1u.plain_default[c2u][0]

    # check key lookup with key directly from keys()
    plain_keys = list(c1u.plain.keys())
    ordered_keys = list(c1u.plain_ordered.keys())
    default_keys = list(c1u.plain_default.keys())
    assert c2u == c1u.plain[plain_keys[0]][0]
    assert c2u == c1u.plain_ordered[ordered_keys[0]][0]
    assert c2u == c1u.plain_default[default_keys[0]][0]
    assert c2u == c1u.plain[plain_keys[0]][0]
    assert c2u == c1u.plain_ordered[ordered_keys[0]][0]
    assert c2u == c1u.plain_default[default_keys[0]][0]


def test_dict_self_cycle():
    g = Group("group")
    c1 = C(42)
    g.elements.append(c1)
    c2 = C(67)
    g.elements.append(c2)
    c1.add(c1, "a")  # cycle to itself
    c1.add(c2, "b")  # c2 does not point to itself nor c1

    assert c1 in c1.plain
    assert c1 in c1.plain_ordered
    assert c1 in c1.plain_default

    gu = pickle_and_unpickle(g)
    c1u = gu.elements[0]
    c2u = gu.elements[1]

    # check existence of keys directly
    # key c1u
    assert c1u in list(c1u.plain.keys())
    assert c1u in list(c1u.plain_ordered.keys())
    assert c1u in list(c1u.plain_default.keys())

    # key c2u
    assert c2u in list(c1u.plain.keys())
    assert c2u in list(c1u.plain_ordered.keys())
    assert c2u in list(c1u.plain_default.keys())

    # check direct key-based lookup

    # key c1u
    assert 42 == c1u.plain[c1u][0].v
    assert 42 == c1u.plain_ordered[c1u][0].v

    assert len(c1u.plain_default) == 2
    assert 42 == c1u.plain_default[c1u][0].v
    # No new entries were created.
    assert len(c1u.plain_default) == 2

    # key c2u
    # succeeds because c2u does not have a cycle to itself
    assert c2u == c1u.plain[c2u][0]
    # succeeds because c2u does not have a cycle to itself
    assert c2u == c1u.plain_ordered[c2u][0]
    # succeeds because c2u does not have a cycle to itself
    assert c2u == c1u.plain_default[c2u][0]
    assert c2u == c1u.plain[c2u][0]
    assert c2u == c1u.plain_ordered[c2u][0]
    assert c2u == c1u.plain_default[c2u][0]

    # check key lookup with key directly from keys()
    # key c1u
    plain_keys = list(c1u.plain.keys())
    ordered_keys = list(c1u.plain_ordered.keys())
    default_keys = list(c1u.plain_default.keys())
    value = 42
    assert value == c1u.plain[plain_keys[0]][0].v
    42 == c1u.plain_ordered[ordered_keys[0]][0].v
    42 == c1u.plain_default[default_keys[0]][0].v

    # key c2u
    # succeeds because c2u does not have a cycle to itself
    assert c2u == c1u.plain[plain_keys[1]][0]
    # succeeds because c2u does not have a cycle to itself
    assert c2u == c1u.plain_ordered[ordered_keys[1]][0]
    assert 67 == c1u.plain_default[default_keys[1]][0].v


def test_dict_mutual_cycle():
    g = Group("group")
    c1 = C(42)
    g.elements.append(c1)
    c2 = C(67)
    g.elements.append(c2)

    c1.add(c2, "a")  # points to c2, which points to c1, forming cycle
    c2.add(c1, "a")  # points to c1 in order to form cycle

    assert c2 in c1.plain
    assert c2 in c1.plain_ordered
    assert c2 in c1.plain_default

    assert c1 in c2.plain
    assert c1 in c2.plain_ordered
    assert c1 in c2.plain_default

    gu = pickle_and_unpickle(g)
    c1u = gu.elements[0]
    c2u = gu.elements[1]

    # check existence of keys directly
    # key c2u
    assert c2u in c1u.plain.keys()
    assert c2u in c1u.plain_ordered.keys()
    assert c2u in c1u.plain_default.keys()

    # key c1u
    assert c1u in list(c2u.plain.keys())
    assert c1u in list(c2u.plain_ordered.keys())
    assert c1u in list(c2u.plain_default.keys())

    # check direct key-based lookup
    # key c2u, succeed because c2u added to c1u after __setstate__
    assert c2u == c1u.plain[c2u][0]
    assert c2u == c1u.plain_ordered[c2u][0]
    assert c2u == c1u.plain_default[c2u][0]

    # key c1u
    assert isinstance(c2u.plain[c1u][0], C)
    assert 42 == c2u.plain[c1u][0].v
    assert isinstance(c2u.plain_ordered[c1u][0], C)

    # succeeds
    assert len(c2u.plain_default) == 1
    assert 42 == c2u.plain_default[c1u][0].v
    # Ensure that no new entry is created by verifying that the length
    # has not changed.
    assert len(c2u.plain_default) == 1

    # check key lookup with key directly from keys()

    # key c2u, succeed because c2u added to c1u after __setstate__
    plain_keys = list(c1u.plain.keys())
    ordered_keys = list(c1u.plain_ordered.keys())
    default_keys = list(c1u.plain_default.keys())
    assert c2u == c1u.plain[plain_keys[0]][0]
    assert c2u == c1u.plain_ordered[ordered_keys[0]][0]
    assert c2u == c1u.plain_default[default_keys[0]][0]

    # key c1u
    plain_keys = list(c2u.plain.keys())
    ordered_keys = list(c2u.plain_ordered.keys())
    default_keys = list(c2u.plain_default.keys())
    assert 42 == c2u.plain[plain_keys[0]][0].v
    assert 42 == c2u.plain_ordered[ordered_keys[0]][0].v
    assert 42 == c2u.plain_default[default_keys[0]][0].v
    assert isinstance(c2u.plain[plain_keys[0]], tuple)
    assert isinstance(c2u.plain_ordered[ordered_keys[0]], tuple)


def test_set_no_cycle():
    g = Group("group")
    d1 = D(42)
    g.elements.append(d1)
    d2 = D(67)
    g.elements.append(d2)
    d1.add(d2)  # d1 points to d1, d2 does not point to anything, no cycles

    assert d2 in d1.plain

    gu = pickle_and_unpickle(g)
    d1u = gu.elements[0]
    d2u = gu.elements[1]

    # check element directly
    assert d2u in d1u.plain
    # check element taken from elements
    assert list(d1u.plain)[0] in d1u.plain


def test_set_self_cycle():
    g = Group("group")
    d1 = D(42)
    g.elements.append(d1)
    d2 = D(67)
    g.elements.append(d2)
    d1.add(d1)  # cycle to itself
    d1.add(d2)  # d1 also points to d2, but d2 does not point to d1

    assert d1 in d1.plain

    gu = pickle_and_unpickle(g)
    d1u = gu.elements[0]
    d2u = gu.elements[1]
    assert d2u is not None

    # check element directly
    assert d1u in d1u.plain
    # check element taken from elements
    assert list(d1u.plain)[0] in d1u.plain
    # succeeds because d2u added to d1u after __setstate__
    assert list(d1u.plain)[1] in d1u.plain


def test_set_mutual_cycle():
    g = Group("group")
    d1 = D(42)
    g.elements.append(d1)
    d2 = D(67)
    g.elements.append(d2)
    d1.add(d2)  # points to d2, which points to d1, forming cycle
    d2.add(d1)  # points to d1 in order to form cycle

    assert d2 in d1.plain
    assert d1 in d2.plain

    gu = pickle_and_unpickle(g)
    d1u = gu.elements[0]
    d2u = gu.elements[1]

    # check element directly
    # succeeds because d2u added to d1u after __setstate__
    assert d2u in d1u.plain
    assert d1u in d2u.plain
    # check element taken from elements
    # succeeds because d2u added to d1u after __setstate__
    assert list(d1u.plain)[0] in d1u.plain
    assert list(d2u.plain)[0] in d2u.plain


import jsonpickle


class Node:
    def __init__(self, name):
        self._name = name
        self._children = []
        self._parent = None

    def add_child(self, child, index=-1):
        if index == -1:
            index = len(self._children)
        self._children.insert(index, child)
        child._parent = self


class Document(Node):
    def __init__(self, name):
        Node.__init__(self, name)

    def __repr__(self):
        return str(self)

    def __str__(self):
        ret_str = 'Document "%s"\n' % self._name
        for c in self._children:
            ret_str += repr(c)
        return ret_str


class Question(Node):
    def __init__(self, name):
        Node.__init__(self, name)

    def __str__(self):
        return f'Question "{self._name}", parent: "{self._parent._name}"\n'

    def __repr__(self):
        return self.__str__()


class Section(Node):
    def __init__(self, name):
        Node.__init__(self, name)

    def __str__(self):
        ret_str = f'Section "{self._name}", parent: "{self._parent._name}"\n'
        for c in self._children:
            ret_str += repr(c)
        return ret_str

    def __repr__(self):
        return self.__str__()


def test_cyclical():
    """Test that we can pickle cyclical data structure

    This test is ensures that we can reference objects which
    first appear within a list (in other words, not a top-level
    object or attribute).  Later children will reference that
    object through its "_parent" field.

    This makes sure that we handle this case correctly.

    """
    document = Document("My Document")
    section1 = Section("Section 1")
    section2 = Section("Section 2")
    question1 = Question("Question 1")
    question2 = Question("Question 2")
    question3 = Question("Question 3")
    question4 = Question("Question 4")
    document.add_child(section1)
    document.add_child(section2)
    section1.add_child(question1)
    section1.add_child(question2)
    section2.add_child(question3)
    section2.add_child(question4)
    pickled = jsonpickle.encode(document)
    unpickled = jsonpickle.decode(pickled)
    assert str(document) == str(unpickled)


"""Test miscellaneous objects from the standard library"""

import uuid

import jsonpickle


def test_random_uuid():
    u = uuid.uuid4()
    encoded = jsonpickle.encode(u)
    decoded = jsonpickle.decode(encoded)

    expect = u.hex
    actual = decoded.hex
    assert expect == actual


def test_known_uuid():
    expect = "28b56adbd18f44e2a5556bba2f23e6f6"
    exemplar = uuid.UUID(expect)
    encoded = jsonpickle.encode(exemplar)
    decoded = jsonpickle.decode(encoded)

    actual = decoded.hex
    assert expect == actual


def test_bytestream():
    expect = (
        b"\x89HDF\r\n\x1a\n\x00\x00\x00\x00\x00\x08\x08\x00"
        b"\x04\x00\x10\x00\x00\x00\x00\x00\x00\x00\x00\x00"
        b"\x00\x00\x00\x00\xff\xff\xff\xff\xff\xff\xff\xffh"
        b"\x848\x00\x00\x00\x00\x00\xff\xff\xff\xff\xff\xff"
        b"\xff\xff\x00\x00\x00\x00\x00\x00\x00\x00`\x00\x00"
        b"\x00\x00\x00\x00\x00\x01\x00\x00\x00\x00\x00\x00"
        b"\x00\x88\x00\x00\x00\x00\x00\x00\x00\xa8\x02\x00"
        b"\x00\x00\x00\x00\x00\x01\x00\x01\x00"
    )
    encoded = jsonpickle.encode(expect)
    actual = jsonpickle.decode(encoded)
    assert expect == actual


"""Wizard tests from petrounias.org

http://www.petrounias.org/articles/2014/09/16/pickling-python-collections-with-non-built-in-type-keys-and-cycles/

Includes functionality to assist with adding compatibility to jsonpickle.

"""

import collections

from jsonpickle import decode, encode


class World:
    def __init__(self):
        self.wizards = []


class Wizard:
    def __init__(self, world, name):
        self.name = name
        self.spells = collections.OrderedDict()
        world.wizards.append(self)

    def __cmp__(self, other):
        for (ka, va), (kb, vb) in zip(self.spells.items(), other.spells.items()):
            cmp_name = cmp(ka.name, kb.name)  # noqa: F821
            if cmp_name != 0:
                print(f"Wizards cmp: {ka.name} != {kb.name}")
                return cmp_name
            for sa, sb in zip(va, vb):
                cmp_spell = cmp(sa, sb)  # noqa: F821
                if cmp_spell != 0:
                    print(f"Spells cmp: {sa.name} != {sb.name}")
                    return cmp_spell
        return cmp(self.name, other.name)  # noqa: F821

    def __eq__(self, other):
        for (ka, va), (kb, vb) in zip(self.spells.items(), other.spells.items()):
            if ka.name != kb.name:
                print(f"Wizards differ: {ka.name} != {kb.name}")
                return False
            for sa, sb in zip(va, vb):
                if sa != sb:
                    print(f"Spells differ: {sa.name} != {sb.name}")
                    return False
        return self.name == other.name

    def __hash__(self):
        return hash("Wizard %s" % self.name)


class Spell:
    def __init__(self, caster, target, name):
        self.caster = caster
        self.target = target
        self.name = name
        try:
            spells = caster.spells[target]
        except KeyError:
            spells = caster.spells[target] = []
        spells.append(self)

    def __cmp__(self, other):
        return (
            cmp(self.name, other.name)  # noqa: F821
            or cmp(self.caster.name, other.caster.name)  # noqa: F821
            or cmp(self.target.name, other.target.name)  # noqa: F821
        )  # noqa: F821

    def __eq__(self, other):
        return (
            self.name == other.name
            and self.caster.name == other.caster.name
            and self.target.name == other.target.name
        )

    def __hash__(self):
        return hash(f"Spell {self.name} by {self.caster.name} on {self.target.name}")


def hashsum(items):
    return sum([hash(x) for x in items])


def compare_spells(a, b):
    for (ka, va), (kb, vb) in zip(a.items(), b.items()):
        if ka != kb:
            print(f"Keys differ: {ka} != {kb}")
            return False
    return True

def test_with_pickling():
    world = World()
    wizard_merlin = Wizard(world, "Merlin")
    wizard_morgana = Wizard(world, "Morgana")
    wizard_morgana_prime = Wizard(world, "Morgana")
    assert wizard_morgana.__dict__ == wizard_morgana_prime.__dict__

    spell_a = Spell(wizard_merlin, wizard_morgana, "magic-missile")
    spell_b = Spell(wizard_merlin, wizard_merlin, "stone-skin")
    spell_c = Spell(wizard_morgana, wizard_merlin, "geas")
    assert wizard_merlin.spells[wizard_morgana][0] == spell_a
    assert wizard_merlin.spells[wizard_merlin][0] == spell_b
    assert wizard_morgana.spells[wizard_merlin][0] == spell_c

    flat_world = encode(world, keys=True)
    u_world = decode(flat_world, keys=True)
    u_wizard_merlin = u_world.wizards[0]
    u_wizard_morgana = u_world.wizards[1]
    morgana_spells_encoded = encode(wizard_morgana.spells, keys=True)
    morgana_spells_decoded = decode(morgana_spells_encoded, keys=True)
    assert wizard_morgana.spells == morgana_spells_decoded

    morgana_encoded = encode(wizard_morgana, keys=True)
    morgana_decoded = decode(morgana_encoded, keys=True)
    assert wizard_morgana == morgana_decoded
    assert hash(wizard_morgana) == hash(morgana_decoded)
    assert wizard_morgana.spells == morgana_decoded.spells
    # Merlin has cast Magic Missile on Morgana, and Stone Skin on himself
    merlin_spells = u_wizard_merlin.spells
    assert merlin_spells[u_wizard_morgana][0].name == "magic-missile"
    assert merlin_spells[u_wizard_merlin][0].name == "stone-skin"
    # Morgana has cast Geas on Merlin
    assert u_wizard_morgana.spells[u_wizard_merlin][0].name == "geas"
    # Merlin's first target was Morgana
    merlin_spells_keys = list(u_wizard_merlin.spells.keys())
    assert merlin_spells_keys[0] in u_wizard_merlin.spells
    assert merlin_spells_keys[0] == u_wizard_morgana
    # Merlin's second target was himself
    assert merlin_spells_keys[1] in u_wizard_merlin.spells
    assert merlin_spells_keys[1] == u_wizard_merlin
    # Morgana's first target was Merlin
    morgana_spells_keys = list(u_wizard_morgana.spells.keys())
    assert morgana_spells_keys[0] in u_wizard_morgana.spells
    assert morgana_spells_keys[0] == u_wizard_merlin
    # Merlin's first spell cast with himself as target is in the dict.
    # First try the lookup with Merlin's instance object
    assert u_wizard_merlin == merlin_spells[u_wizard_merlin][0].target
    # Next try the lookup with the object from the dictionary keys.
    assert u_wizard_merlin == merlin_spells[merlin_spells_keys[1]][0].target
    # Ensure Merlin's object is unique and consistently hashed.
    assert id(u_wizard_merlin) == id(merlin_spells_keys[1])
    assert hash(u_wizard_merlin) == hash(merlin_spells_keys[1])


import sys

import jsonpickle


def _roundtrip(obj):
    """Verify object equality after encoding and decoding to/from jsonpickle"""
    pickled = jsonpickle.encode(obj)
    unpickled = jsonpickle.decode(pickled)
    assert obj == unpickled


def test_zoneinfo():
    """zoneinfo objects can roundtrip"""
    if sys.version_info < (3, 9):
        return
    from zoneinfo import ZoneInfo

    _roundtrip(ZoneInfo("Australia/Brisbane"))
