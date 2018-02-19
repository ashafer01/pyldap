"""Base classes for syntax rules and matching rules"""

from __future__ import absolute_import
from .exceptions import InvalidSyntaxError, LDAPSchemaError
import re
import six


## Syntax Rules

_oid_syntax_rules = {}
_oid_syntax_rule_objects = {}


def get_syntax_rule(oid):
    obj = _oid_syntax_rule_objects.get(oid)
    if not obj:
        obj = _oid_syntax_rules[oid]()
    return obj


class MetaSyntaxRule(type):
    """Metaclass registering OIDs on subclasses"""
    def __new__(meta, name, bases, dct):
        oid = dct.get('OID')
        cls = type.__new__(meta, name, bases, dct)
        if oid:
            if oid in _oid_syntax_rules:
                raise LDAPSchemaError('Duplicate OID in syntax rule declaration')
            _oid_syntax_rules[oid] = cls
        return cls


@six.add_metaclass(MetaSyntaxRule)
class SyntaxRule(object):
    """Base class for all syntax rules"""
    def __init__(self):
        oid = getattr(self, 'OID', None)
        if oid:
            if oid in _oid_syntax_rule_objects:
                raise LDAPSchemaError('Multiple instantiations of syntax rule with OID {0}'.format(oid))
            _oid_syntax_rule_objects[oid] = self

    def validate(self, s):
        raise NotImplementedError()


class RegexSyntaxRule(SyntaxRule):
    """For validating rules based on a regular expression
     Subclasses must define the `regex` attribute
    """
    def __init__(self):
        self.compiled_re = re.compile(self.regex)
        SyntaxRule.__init__(self)

    def validate(self, s):
        m = self.compiled_re.match(s)
        if m:
            return m
        else:
            raise InvalidSyntaxError('Not a valid {0}: {1}'.format(self.DESC, s))


## Matching Rules


_oid_matching_rules = {}
_name_matching_rules = {}
_oid_matching_rule_objects = {}
_name_matching_rule_objects = {}


def get_matching_rule(ident):
    """Obtains matching rule instance for name or OID"""
    if ident[0].isdigit():
        cls_dict = _oid_matching_rules
        obj_dict = _oid_matching_rule_objects
    else:
        cls_dict = _name_matching_rules
        obj_dict = _name_matching_rule_objects
    obj = obj_dict.get(ident)
    if not obj:
        obj = cls_dict[ident]()
    return obj


class MetaMatchingRule(type):
    """Metaclass registering OIDs and NAMEs on subclasses"""
    def __new__(meta, clsname, bases, dct):
        oid = dct.get('OID')
        names = dct.get('NAME', ())
        if isinstance(names, six.string_types):
            names = (names,)
            dct['NAME'] = names
        cls = type.__new__(meta, clsname, bases, dct)
        if oid:
            if oid in _oid_matching_rules:
                raise LDAPSchemaError('Duplicate OID {0} in matching rule declaration'.format(oid))
            _oid_matching_rules[oid] = cls
        for name in names:
            if name in _name_matching_rules:
                raise LDAPSchemaError('Duplicate name {0} in matching rule declaration'.format(name))
            _name_matching_rules[name] = cls
        return cls


@six.add_metaclass(MetaMatchingRule)
class MatchingRule(object):
    """Base class for all matching rules"""

    def __init__(self):
        oid = getattr(self, 'OID', None)
        if oid:
            if oid in _oid_matching_rule_objects:
                raise LDAPSchemaError('Multiple instantiations of matching rule with OID {0}'.format(oid))
            _oid_matching_rule_objects[oid] = self
        names = getattr(self, 'NAME', ())
        for name in names:
            if name in _name_matching_rule_objects:
                raise LDAPSchemaError('Multiple instantiations of matching rule with name {0}'.format(name))
            _name_matching_rule_objects[name] = self

    def validate(self, value):
        """Perform validation according to the matching rule's syntax"""
        return get_syntax_rule(self.SYNTAX).validate(value)

    def prepare(self, value):
        """Prepare a string for matching"""
        for method in getattr(self, 'prep_methods', ()):
            value = method(value)
        return value

    def do_match(self, attribute_value, assertion_value):
        """Perform the match operation"""
        raise NotImplementedError()

    def match(self, attribute_value, assertion_value):
        """Prepare values and perform the match operation. Assumes values have
         already been validated.
        """
        attribute_value = self.prepare(attribute_value)
        assertion_value = self.prepare(assertion_value)
        return self.do_match(attribute_value, assertion_value)


# Note: currently only implementing equality matching rules since there is no
# use for ordering or substring matching rules for correct functioning of the
# current codebase. Any forseeable use for other types of rules would be in
# support of new features not currently planned.

class EqualityMatchingRule(MatchingRule):
    """Base class for all EQUALITY matching rules"""

    def do_match(self, attribute_value, assertion_value):
        """Perform equality matching"""
        return (attribute_value == assertion_value)
