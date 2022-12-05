import dataclasses
import enum
import pathlib
from collections import namedtuple
from typing import List, Union

import pytest

from autodict import AutoDict, dictable
from autodict.autodict import Dictable, from_dictable, to_dictable
from autodict.errors import UnableFromDict, UnableToDict


@dictable
class Normal:
    def __init__(self, str_value, int_value):
        self.str_value = str_value
        self.int_value = int_value

    def __eq__(self, other):
        return isinstance(other, Normal) and \
            self.str_value == other.str_value and \
            self.int_value == other.int_value

    def __str__(self):
        return f'({self.str_value}, {self.int_value})'


@dictable(name='SomeA')
class CustomName:
    def __init__(self, str_value, int_value):
        self.str_value = str_value
        self.int_value = int_value

    def __eq__(self, other):
        return isinstance(other, CustomName) and \
            self.str_value == other.str_value and \
            self.int_value == other.int_value


class Unregistered:
    def __init__(self, str_value, int_value):
        self.str_value = str_value
        self.int_value = int_value

    def __eq__(self, other):
        return isinstance(other, Unregistered) and \
            self.str_value == other.str_value and \
            self.int_value == other.int_value


@dictable
class WithEmptyConstructor:
    def __init__(self):
        self._protected_value = ''
        self.__private_value = 0

    @staticmethod
    def create(protected_value, private_value):
        self = WithEmptyConstructor()
        self._protected_value = protected_value
        self.__private_value = private_value
        return self

    def __eq__(self, other):
        return isinstance(other, WithEmptyConstructor) and \
            self._protected_value == other._protected_value and \
            self.__private_value == other.__private_value


@dictable
class WithHiddenMember:
    def __init__(self, protected_value, private_value):
        self._protected_value = protected_value
        self.__private_value = private_value

    def __eq__(self, other):
        return isinstance(other, WithHiddenMember) and \
            self._protected_value == other._protected_value and \
            self.__private_value == other.__private_value


@dictable
class WithInheritedHiddenMember(WithHiddenMember):
    def __init__(self, protected_value, private_value):
        super().__init__(protected_value, private_value)


@dictable
class NestDictable:
    a: Normal

    def __init__(self, a, count):
        self.a = a
        self.count = count

    def __eq__(self, other):
        return self.a == other.a and self.count == other.count


@dictable
class NestUnDictable:
    a: Unregistered

    def __init__(self, a, count):
        self.a = a
        self.count = count

    def __eq__(self, other):
        return isinstance(other, NestUnDictable) and \
            self.a == other.a and \
            self.count == other.count


class UnDictableNest:
    a: Normal

    def __init__(self, a, count):
        self.a = a
        self.count = count

    def __eq__(self, other):
        return isinstance(other, UnDictableNest) and \
            self.a == other.a and \
            self.count == other.count


@dictable
class AnnotatedList:
    b_list: List[NestDictable]

    def __init__(self, b_list, count):
        self.b_list = b_list
        self.count = count

    def __eq__(self, other):
        return isinstance(other, AnnotatedList) and \
            self.b_list == other.b_list and \
            self.count == other.count


@dictable
class AnnotatedUnion:
    union_value: Union[str, Normal, List[str]]

    def __init__(self, union_value):
        self.union_value = union_value

    def __eq__(self, other):
        return isinstance(other, AnnotatedUnion) and \
            self.union_value == other.union_value


@dictable
class AnnotatedListUnion:
    value: List[Union[str, Normal, List[str]]]

    def __init__(self, value):
        self.value = value

    def __eq__(self, other) -> bool:
        return isinstance(other, AnnotatedListUnion) and \
            self.value == other.value


try:
    from typing import Literal

    Literals = Literal['w+', 'r+']

except ImportError:
    Literal = str
    Literals = Literal


@dictable
class AnnotatedLiteral:
    value: Literals

    def __init__(self, value):
        self.value = value

    def __eq__(self, other):
        return isinstance(other, AnnotatedLiteral) and \
            self.value == other.value


@dictable
class AnnotatedRef:
    b: 'NestDictable'
    b_list: List['NestDictable']

    def __init__(self, b, b_list, count):
        self.b = b
        self.b_list = b_list
        self.count = count

    def __eq__(self, other):
        return isinstance(other, AnnotatedRef) and \
            self.b == other.b and \
            self.b_list == other.b_list and \
            self.count == other.count


@dictable
class Color(enum.Enum):
    Black = 1
    Red = 2


@dictable
class AnnotatedSpecialStd:
    path: pathlib.Path
    color: Color

    def __init__(self, path, color):
        self.path = path
        self.color = color

    def __eq__(self, other):
        return isinstance(other, AnnotatedSpecialStd) and \
            self.path == other.path and \
            self.color == other.color


@dataclasses.dataclass
class NativeDataclass:
    str_value: str
    list_value: List[int]


@dataclasses.dataclass
class DataclassWithField:
    init_value: str
    init_variable: dataclasses.InitVar[int] = 0
    post_init_value: int = dataclasses.field(init=False)
    default_value: int = dataclasses.field(default=10)

    def __post_init__(self, init_variable):
        self.post_init_value = self.default_value + init_variable


GoodCase = namedtuple('GoodCase', 'obj,dic,with_cls,strict,name')

BadCase = namedtuple('BadCase', 'obj,dic,with_cls,strict,exc,raises,name')


def generate_good_cases() -> List[GoodCase]:
    return [
        GoodCase(
            name='with embedded class info',
            obj=Normal(str_value='limo', int_value=10),
            dic={'str_value': 'limo', 'int_value': 10, '@': 'Normal', },
            with_cls=True,
            strict=True,
        ),
        GoodCase(
            name='without embedded class info',
            obj=Normal(str_value='limo', int_value=10),
            dic={'str_value': 'limo', 'int_value': 10, },
            with_cls=False,
            strict=True,
        ),
        GoodCase(
            name='with embedded class info but customized name',
            obj=CustomName(str_value='limo', int_value=10),
            dic={'str_value': 'limo', 'int_value': 10, '@': 'SomeA', },
            with_cls=True,
            strict=True,
        ),
        GoodCase(
            name='allow un-dictable without embedding class info',
            obj=Unregistered(str_value='limo', int_value=10),
            dic=Unregistered(str_value='limo', int_value=10),
            with_cls=False,
            strict=False,
        ),
        GoodCase(
            name='allow un-dictable with embedded class info',
            obj={'str_value': 'limo', 'int_value': 10, '@': 'Unregistered'},
            dic={'str_value': 'limo', 'int_value': 10, '@': 'Unregistered'},
            with_cls=True,
            strict=False,
        ),
        GoodCase(
            name='when target is a dict itself',
            obj={'str_value': 'limo', 'int_value': 10},
            dic={'str_value': 'limo', 'int_value': 10},
            with_cls=True,
            strict=True,
        ),
        GoodCase(
            name='when has hidden fields while constructor has no arg',
            obj=WithEmptyConstructor.create('limo', 20),
            dic={'_protected_value': 'limo',
                 '_WithEmptyConstructor__private_value': 20,
                 '@': 'WithEmptyConstructor'},
            with_cls=True,
            strict=True,
        ),
        GoodCase(
            name='when has hidden fields while constructor has args',
            obj=WithHiddenMember('limo', 20),
            dic={'_protected_value': 'limo',
                 '_WithHiddenMember__private_value': 20,
                 '@': 'WithHiddenMember'},
            with_cls=True,
            strict=True,
        ),
        GoodCase(
            name='when has inherited hidden fields while constructor has args',
            obj=WithInheritedHiddenMember('limo', 20),
            dic={'_protected_value': 'limo',
                 '_WithHiddenMember__private_value': 20,
                 '@': 'WithInheritedHiddenMember'},
            with_cls=True,
            strict=True,
        ),
        GoodCase(
            name='nested dictable with class annotation',
            obj=NestDictable(a=Normal(str_value='limo', int_value=10),
                             count=20),
            dic={'a': {'str_value': 'limo', 'int_value': 10, '@': 'Normal'},
                 'count': 20,
                 '@': 'NestDictable'},
            with_cls=True,
            strict=True,
        ),
        GoodCase(
            name='nested dictable with generic list',
            obj=AnnotatedList(b_list=[
                NestDictable(a=Normal(str_value='limo', int_value=20),
                             count=3)],
                count=4),
            dic={'@': 'AnnotatedList',
                 'b_list': [{'@': 'NestDictable',
                             'a': {'@': 'Normal', 'int_value': 20,
                                   'str_value': 'limo'},
                             'count': 3}],
                 'count': 4},
            with_cls=True,
            strict=False,
        ),
        GoodCase(
            name='nested dictable with generic union - 1',
            obj=AnnotatedUnion(union_value='string value'),
            dic={'union_value': 'string value'},
            with_cls=False,
            strict=False,
        ),
        GoodCase(
            name='nested dictable with generic union - 2',
            obj=AnnotatedUnion(union_value=Normal(str_value='o', int_value=0)),
            dic={'union_value': {'str_value': 'o',
                                 'int_value': 0}},
            with_cls=False,
            strict=False,
        ),
        GoodCase(
            name='nested dictable with generic union - 3',
            obj=AnnotatedUnion(union_value=['string', 'value']),
            dic={'union_value': ['string', 'value']},
            with_cls=False,
            strict=False,
        ),
        GoodCase(
            name='nested dictable with generic list union',
            obj=AnnotatedListUnion(
                value=['string', Normal(str_value='o', int_value=0),
                       ['string', 'value']]),
            dic={'value': ['string',
                           {'str_value': 'o',
                            'int_value': 0},
                           ['string', 'value']]},
            with_cls=False,
            strict=False,
        ),
        GoodCase(
            name='nested dictable with generic literal',
            obj=AnnotatedLiteral(value='w+'),
            dic={'value': 'w+'},
            with_cls=False,
            strict=False,
        ),
        GoodCase(
            name='nested dictable with class annotation string',
            obj=AnnotatedRef(
                b=NestDictable(a=Normal(str_value='limo', int_value=10),
                               count=2),
                b_list=[NestDictable(a=Normal(str_value='limo', int_value=20),
                                     count=3)],
                count=4),
            dic={'@': 'AnnotatedRef',
                 'b': {'@': 'NestDictable',
                       'a': {'@': 'Normal', 'int_value': 10,
                             'str_value': 'limo'},
                       'count': 2},
                 'b_list': [{'@': 'NestDictable',
                             'a': {'@': 'Normal', 'int_value': 20,
                                   'str_value': 'limo'},
                             'count': 3}],
                 'count': 4},
            with_cls=True,
            strict=False,
        ),
        GoodCase(
            name='allow dictable has a non-dictable field',
            obj=NestUnDictable(a=Unregistered(str_value='limo', int_value=10),
                               count=20),
            dic={
                'a': Unregistered(str_value='limo', int_value=10),
                'count': 20,
                '@': 'NestUnDictable'
            },
            with_cls=True,
            strict=False,
        ),
        GoodCase(
            name='allow non-dictable has a dictable field',
            obj=UnDictableNest(a=Normal(str_value='limo', int_value=10),
                               count=2),
            dic=UnDictableNest(a=Normal(str_value='limo', int_value=10),
                               count=2),
            with_cls=True,
            strict=False,
        ),
        GoodCase(
            name='nested dictable with special std types',
            obj=AnnotatedSpecialStd(path=pathlib.Path('/home/limo/.bashrc'),
                                    color=Color.Red),
            dic={'@': 'AnnotatedSpecialStd',
                 'path': '/home/limo/.bashrc',
                 'color': {
                     '@': 'Color',
                     'value': Color.Red.value,
                     'name': Color.Red.name
                 }},
            with_cls=True,
            strict=False,
        ),
        GoodCase(
            name='native support to dataclass',
            obj=NativeDataclass(str_value='limo', list_value=[10, 20]),
            dic={'str_value': 'limo',
                 'list_value': [10, 20]},
            with_cls=False,
            strict=True,
        ),
        GoodCase(
            name='dataclass with fields',
            obj=DataclassWithField(init_value='A', init_variable=10,
                                   default_value=20),
            dic={'init_value': 'A', 'post_init_value': 30, 'default_value': 20},
            with_cls=False,
            strict=True,
        )
    ]


def generate_bad_cases():
    return [
        BadCase(
            name='unable to_dict in strict mode',
            obj=Unregistered(str_value='limo', int_value=10),
            dic=None,
            with_cls=True,
            strict=True,
            exc=UnableToDict,
            raises=dict(match='.*Unregistered.*'),
        ),
        BadCase(
            name='unable from_dict in strict mode without embedded class info',
            obj=None,
            dic={'str_value': 'limo', 'int_value': 10},
            with_cls=Unregistered,
            strict=True,
            exc=UnableFromDict,
            raises=dict(match='.*Unregistered.*'),
        ),
        BadCase(
            name='unable from_dict in strict mode with embedded class info',
            obj=None,
            dic={'str_value': 'limo', 'int_value': 10, '@': 'Unregistered'},
            with_cls=None,
            strict=True,
            exc=UnableFromDict,
            raises=dict(match='.*Unregistered.*'),
        ),
        BadCase(
            name='panic if nested un-dictable when to_dict(.., strict)',
            obj=NestUnDictable(Unregistered(str_value='limo', int_value=10),
                               count=20),
            dic=None,
            with_cls=True,
            strict=True,
            exc=UnableToDict,
            raises=dict(match='.*Unregistered.*'),
        ),
        BadCase(
            name='panic if nested un-dictable when from_dict(.., strict, cls)',
            obj=None,
            dic={
                'a': {'str_value': 'limo', 'int_value': 10},
                'count': 10,
            },
            with_cls=NestUnDictable,
            strict=True,
            exc=UnableFromDict,
            raises=dict(match='.*Unregistered.*'),
        ),
        BadCase(
            name='panic if nested un-dictable when from_dict(.., strict)',
            obj=None,
            dic={
                'a': {'str_value': 'limo', 'int_value': 10,
                      '@': 'Unregistered'},
                'count': 10,
                '@': 'NestUnDictable'
            },
            with_cls=None,
            strict=True,
            exc=UnableFromDict,
            raises=dict(match='.*Unregistered.*'),
        ),
        BadCase(
            name='panic if wrapped un-dictable when to_dict(.., strict)',
            obj=UnDictableNest(Normal(str_value='limo', int_value=10),
                               count=20),
            dic=None,
            with_cls=True,
            strict=True,
            exc=UnableToDict,
            raises=dict(match='.*UnDictableNest.*'),
        ),
        BadCase(
            name='panic if wrapped un-dictable when from_dict(.., strict, cls)',
            obj=None,
            dic={
                'a': {'str_value': 'limo', 'int_value': 10},
                'count': 10,
            },
            with_cls=UnDictableNest,
            strict=True,
            exc=UnableFromDict,
            raises=dict(match='.*UnDictableNest.*'),
        ),
        BadCase(
            name='panic if wrapped un-dictable when from_dict(.., strict)',
            obj=None,
            dic={
                'a': {'str_value': 'limo', 'int_value': 10, '@': 'Normal'},
                'count': 10,
                '@': 'UnDictableNest'
            },
            with_cls=None,
            strict=True,
            exc=UnableFromDict,
            raises=dict(match='.*UnDictableNest.*'),
        ),
    ]


def case_name(case):
    return case.name


class TestAnnotate:
    @pytest.mark.parametrize('case', generate_good_cases(), ids=case_name)
    def test_to_dict(self, case: GoodCase):
        assert AutoDict.to_dict(case.obj, with_cls=case.with_cls,
                                strict=case.strict) == case.dic

    @pytest.mark.parametrize('case', generate_good_cases(), ids=case_name)
    def test_from_dict(self, case: GoodCase):
        cls = None if case.with_cls else type(case.obj)
        output_obj = AutoDict.from_dict(case.dic, cls=cls, strict=case.strict)
        assert output_obj == case.obj

    @pytest.mark.parametrize('case', generate_bad_cases(), ids=case_name)
    def test_failed_to_or_from_dict(self, case: BadCase):
        with pytest.raises(case.exc, **case.raises):
            if case.dic is None:
                AutoDict.to_dict(case.obj, case.with_cls, strict=case.strict)
            elif case.obj is None:
                AutoDict.from_dict(case.dic, case.with_cls, strict=case.strict)

    @to_dictable
    class PartialTo:
        def __init__(self, str_value, int_value):
            self.str_value = str_value
            self.int_value = int_value

    def test_to_dictable_to_dict(self):
        f = TestAnnotate.PartialTo(str_value='limo', int_value=10)
        dict_f = AutoDict.to_dict(f)

        assert dict_f == {'str_value': 'limo', 'int_value': 10,
                          '@': 'PartialTo'}

    def test_to_dictable_from_dict(self):
        dict_f = {'str_value': 'limo', 'int_value': 10, '@': 'PartialTo'}

        with pytest.raises(UnableFromDict, match='.*PartialTo.*'):
            AutoDict.from_dict(dict_f)

    @from_dictable
    class PartialFrom:
        def __init__(self, str_value, int_value):
            self.str_value = str_value
            self.int_value = int_value

        def __eq__(self, other):
            return isinstance(other, TestAnnotate.PartialFrom) and \
                self.str_value == other.str_value and \
                self.int_value == other.int_value

    def test_from_dictable_from_dict(self):
        dict_g = {'str_value': 'limo', 'int_value': 10, '@': 'PartialFrom'}

        g = AutoDict.from_dict(dict_g, TestAnnotate.PartialFrom)
        assert g == TestAnnotate.PartialFrom(str_value='limo', int_value=10)

    def test_from_dictable_to_dict(self):
        g = TestAnnotate.PartialFrom(str_value='limo', int_value=10)

        with pytest.raises(UnableToDict, match='.*PartialFrom.*'):
            AutoDict.to_dict(g)

    @to_dictable
    @from_dictable
    class PartialBoth:
        def __init__(self, str_value, int_value):
            self.str_value = str_value
            self.int_value = int_value

        def __eq__(self, other):
            return isinstance(other, TestAnnotate.PartialBoth) and \
                self.str_value == other.str_value and \
                self.int_value == other.int_value

    def test_to_from_dictable(self):
        h = TestAnnotate.PartialBoth(str_value='limo', int_value=10)
        dict_h = AutoDict.to_dict(h)

        assert dict_h == {'str_value': 'limo', 'int_value': 10,
                          '@': 'PartialBoth'}
        output_h = AutoDict.from_dict(dict_h)
        assert h == output_h


class TestDerive:
    class General(Dictable):
        def __init__(self, str_value, int_value):
            self.str_value = str_value
            self.int_value = int_value

        def __eq__(self, other):
            return isinstance(other, TestDerive.General) and \
                self.str_value == other.str_value and \
                self.int_value == other.int_value

    def test_derive_without_overwritten(self):
        f = TestDerive.General(str_value='limo', int_value=10)

        dict_f = AutoDict.to_dict(f)
        assert dict_f == {
            'str_value': 'limo', 'int_value': 10, '@': 'General'
        }

        output_f = AutoDict.from_dict(dict_f, TestDerive.General)
        assert f == output_f

    class CustomName(Dictable, name='SomeF'):
        def __init__(self, str_value, int_value):
            self.str_value = str_value
            self.int_value = int_value

        def __eq__(self, other):
            return isinstance(other, TestDerive.General) and \
                self.str_value == other.str_value and \
                self.int_value == other.int_value

    def test_derive_without_overwritten_but_customized_name(self):
        f = TestDerive.CustomName(str_value='limo', int_value=10)

        dict_f = AutoDict.to_dict(f)
        assert dict_f == {
            'str_value': 'limo', 'int_value': 10, '@': 'SomeF'
        }

        output_f = AutoDict.from_dict(dict_f, TestDerive.General)
        assert f == output_f

    class OverrideBoth(Dictable):
        def __init__(self):
            self.str_value = ''
            self.int_value = 0

        def __eq__(self, other):
            return isinstance(other, TestDerive.OverrideBoth) and \
                self.str_value == other.str_value and \
                self.int_value == other.int_value

        @classmethod
        def _from_dict(cls, dic: dict) -> 'TestDerive.OverrideBoth':
            g = TestDerive.OverrideBoth()
            g.str_value = dic['str_value']
            g.int_value = dic['int_value']
            return g

        def _to_dict(self) -> dict:
            return {
                'str_value': self.str_value,
                'int_value': self.int_value
            }

    def test_derive_with_overwritten(self):
        g = TestDerive.OverrideBoth()
        g.str_value = 'limo'
        g.int_value = 10

        dict_g = AutoDict.to_dict(g)
        assert dict_g == {
            'str_value': 'limo', 'int_value': 10, '@': 'OverrideBoth'
        }

        output_g = AutoDict.from_dict(dict_g, TestDerive.OverrideBoth)
        assert g == output_g

    class NestedOverride(Dictable):
        g: 'TestDerive.OverrideBoth'

        def __init__(self):
            self.g = TestDerive.OverrideBoth()
            self.count = 0

        def __eq__(self, other):
            return self.g == other.g and \
                self.count == other.count

        @classmethod
        def _from_dict(cls, dic: dict) -> 'TestDerive.NestedOverride':
            h = TestDerive.NestedOverride()
            h.g = dic['g']
            h.count = dic['count']
            return h

        def _to_dict(self) -> dict:
            return {
                'g': self.g,
                'count': self.count
            }

    def test_nested_derive_with_overwritten(self):
        h = TestDerive.NestedOverride()
        h.g = TestDerive.OverrideBoth()
        h.g.str_value = 'limo'
        h.g.int_value = 10
        h.count = 20

        dict_h = AutoDict.to_dict(h)
        assert dict_h == {
            'g': {'str_value': 'limo', 'int_value': 10, '@': 'OverrideBoth'},
            'count': 20,
            '@': 'NestedOverride'
        }

        output_h = AutoDict.from_dict(dict_h, TestDerive.NestedOverride)
        assert h == output_h
