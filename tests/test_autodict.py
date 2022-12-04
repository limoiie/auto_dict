import dataclasses
import enum
import pathlib
from collections import namedtuple
from typing import List

import pytest

from autodict import AutoDict, dictable
from autodict.autodict import Dictable, from_dictable, to_dictable
from autodict.errors import UnableFromDict, UnableToDict


# todo: duplicate all annotator-style classes in derive style, and reuse cases
@dictable
class A:
    def __init__(self, str_value, int_value):
        self.str_value = str_value
        self.int_value = int_value

    def __eq__(self, other):
        return isinstance(other, A) and \
            self.str_value == other.str_value and \
            self.int_value == other.int_value

    def __str__(self):
        return f'({self.str_value}, {self.int_value})'


@dictable(name='SomeA')
class A1:
    def __init__(self, str_value, int_value):
        self.str_value = str_value
        self.int_value = int_value

    def __eq__(self, other):
        return isinstance(other, A1) and \
            self.str_value == other.str_value and \
            self.int_value == other.int_value


class A2:
    def __init__(self, str_value, int_value):
        self.str_value = str_value
        self.int_value = int_value

    def __eq__(self, other):
        return isinstance(other, A2) and \
            self.str_value == other.str_value and \
            self.int_value == other.int_value


@dictable
class A3:
    def __init__(self):
        self._protected_value = ''
        self.__private_value = 0

    @staticmethod
    def create(protected_value, private_value):
        self = A3()
        self._protected_value = protected_value
        self.__private_value = private_value
        return self

    def __eq__(self, other):
        return isinstance(other, A3) and \
            self._protected_value == other._protected_value and \
            self.__private_value == other.__private_value


@dictable
class A4:
    def __init__(self, protected_value, private_value):
        self._protected_value = protected_value
        self.__private_value = private_value

    def __eq__(self, other):
        return isinstance(other, A4) and \
            self._protected_value == other._protected_value and \
            self.__private_value == other.__private_value


@dictable
class A5(A4):
    def __init__(self, protected_value, private_value):
        super().__init__(protected_value, private_value)


@dictable
class B:
    a: A

    def __init__(self, a, count):
        self.a = a
        self.count = count

    def __eq__(self, other):
        return self.a == other.a and self.count == other.count


@dictable
class B2:
    a: A2

    def __init__(self, a, count):
        self.a = a
        self.count = count

    def __eq__(self, other):
        return isinstance(other, B2) and \
            self.a == other.a and \
            self.count == other.count


class B3:
    a: A

    def __init__(self, a, count):
        self.a = a
        self.count = count

    def __eq__(self, other):
        return isinstance(other, B3) and \
            self.a == other.a and \
            self.count == other.count


@dictable
class B4:
    b_list: List[B]

    def __init__(self, b_list, count):
        self.b_list = b_list
        self.count = count

    def __eq__(self, other):
        return isinstance(other, B4) and \
            self.b_list == other.b_list and \
            self.count == other.count


@dictable
class B5:
    b: 'B'
    b_list: List['B']

    def __init__(self, b, b_list, count):
        self.b = b
        self.b_list = b_list
        self.count = count

    def __eq__(self, other):
        return isinstance(other, B5) and \
            self.b == other.b and \
            self.b_list == other.b_list and \
            self.count == other.count


@dictable
class Color(enum.Enum):
    Black = 1
    Red = 2


@dictable
class B6:
    path: pathlib.Path
    color: Color

    def __init__(self, path, color):
        self.path = path
        self.color = color

    def __eq__(self, other):
        return isinstance(other, B6) and \
            self.path == other.path and \
            self.color == other.color


@dataclasses.dataclass
class D:
    str_value: str
    int_values: List[int]


good_case = namedtuple('GC', 'obj,dic,with_cls,strict,name')

bad_case = namedtuple('BC', 'obj,dic,with_cls,strict,exc,raises,name')


def generate_good_cases() -> List[good_case]:
    return [
        good_case(
            name='with embedded class info',
            obj=A(str_value='limo', int_value=10),
            dic={'str_value': 'limo', 'int_value': 10, '@': 'A', },
            with_cls=True,
            strict=True,
        ),
        good_case(
            name='without embedded class info',
            obj=A(str_value='limo', int_value=10),
            dic={'str_value': 'limo', 'int_value': 10, },
            with_cls=False,
            strict=True,
        ),
        good_case(
            name='with embedded class info but customized name',
            obj=A1(str_value='limo', int_value=10),
            dic={'str_value': 'limo', 'int_value': 10, '@': 'SomeA', },
            with_cls=True,
            strict=True,
        ),
        good_case(
            name='allow un-dictable without embedding class info',
            obj=A2(str_value='limo', int_value=10),
            dic=A2(str_value='limo', int_value=10),
            with_cls=False,
            strict=False,
        ),
        good_case(
            name='allow un-dictable with embedded class info',
            obj={'str_value': 'limo', 'int_value': 10, '@': 'A2'},
            dic={'str_value': 'limo', 'int_value': 10, '@': 'A2'},
            with_cls=True,
            strict=False,
        ),
        good_case(
            name='when target is a dict itself',
            obj={'str_value': 'limo', 'int_value': 10},
            dic={'str_value': 'limo', 'int_value': 10},
            with_cls=True,
            strict=True,
        ),
        good_case(
            name='when has hidden fields while constructor has no arg',
            obj=A3.create('limo', 20),
            dic={
                '_protected_value': 'limo',
                '_A3__private_value': 20,
                '@': 'A3'
            },
            with_cls=True,
            strict=True,
        ),
        good_case(
            name='when has hidden fields while constructor has args',
            obj=A4('limo', 20),
            dic={
                '_protected_value': 'limo',
                '_A4__private_value': 20,
                '@': 'A4'
            },
            with_cls=True,
            strict=True,
        ),
        good_case(
            name='when has inherited hidden fields while constructor has args',
            obj=A5('limo', 20),
            dic={
                '_protected_value': 'limo',
                '_A4__private_value': 20,
                '@': 'A5'
            },
            with_cls=True,
            strict=True,
        ),
        good_case(
            name='nested dictable with class annotation',
            obj=B(a=A(str_value='limo', int_value=10), count=20),
            dic={
                'a': {'str_value': 'limo', 'int_value': 10, '@': 'A'},
                'count': 20,
                '@': 'B'
            },
            with_cls=True,
            strict=True,
        ),
        good_case(
            name='nested dictable with generic class annotation',
            obj=B4(b_list=[B(a=A(str_value='limo', int_value=20), count=3)],
                   count=4),
            dic={'@': 'B4',
                 'b_list': [{'@': 'B',
                             'a': {'@': 'A', 'int_value': 20,
                                   'str_value': 'limo'},
                             'count': 3}],
                 'count': 4},
            with_cls=True,
            strict=False,
        ),
        good_case(
            name='nested dictable with class annotation string',
            obj=B5(b=B(a=A(str_value='limo', int_value=10), count=2),
                   b_list=[B(a=A(str_value='limo', int_value=20), count=3)],
                   count=4),
            dic={'@': 'B5',
                 'b': {'@': 'B',
                       'a': {'@': 'A', 'int_value': 10, 'str_value': 'limo'},
                       'count': 2},
                 'b_list': [{'@': 'B',
                             'a': {'@': 'A', 'int_value': 20,
                                   'str_value': 'limo'},
                             'count': 3}],
                 'count': 4},
            with_cls=True,
            strict=False,
        ),
        good_case(
            name='allow dictable has a non-dictable field',
            obj=B2(a=A2(str_value='limo', int_value=10), count=20),
            dic={
                'a': A2(str_value='limo', int_value=10),
                'count': 20,
                '@': 'B2'
            },
            with_cls=True,
            strict=False,
        ),
        good_case(
            name='allow non-dictable has a dictable field',
            obj=B3(a=A(str_value='limo', int_value=10), count=2),
            dic=B3(a=A(str_value='limo', int_value=10), count=2),
            with_cls=True,
            strict=False,
        ),
        good_case(
            name='nested dictable with special std types',
            obj=B6(path=pathlib.Path('/home/limo/.bashrc'),
                   color=Color.Red),
            dic={'@': 'B6',
                 'path': '/home/limo/.bashrc',
                 'color': {
                     '@': 'Color',
                     'value': Color.Red.value,
                     'name': Color.Red.name
                 }},
            with_cls=True,
            strict=False,
        ),
        good_case(
            name='native support to dataclasses',
            obj=D(str_value='limo', int_values=[10, 20]),
            dic={'str_value': 'limo',
                 'int_values': [10, 20]},
            with_cls=False,
            strict=True,
        ),
    ]


def generate_bad_cases():
    return [
        bad_case(
            name='unable to_dict in strict mode',
            obj=A2(str_value='limo', int_value=10),
            dic=None,
            with_cls=True,
            strict=True,
            exc=UnableToDict,
            raises=dict(match='.*A2.*'),
        ),
        bad_case(
            name='unable from_dict in strict mode without embedded class info',
            obj=None,
            dic={'str_value': 'limo', 'int_value': 10},
            with_cls=A2,
            strict=True,
            exc=UnableFromDict,
            raises=dict(match='.*A2.*'),
        ),
        bad_case(
            name='unable from_dict in strict mode with embedded class info',
            obj=None,
            dic={'str_value': 'limo', 'int_value': 10, '@': 'A2'},
            with_cls=None,
            strict=True,
            exc=UnableFromDict,
            raises=dict(match='.*A2.*'),
        ),
        bad_case(
            name='panic if nested un-dictable when to_dict(.., strict)',
            obj=B2(A2(str_value='limo', int_value=10), count=20),
            dic=None,
            with_cls=True,
            strict=True,
            exc=UnableToDict,
            raises=dict(match='.*A2.*'),
        ),
        bad_case(
            name='panic if nested un-dictable when from_dict(.., strict, cls)',
            obj=None,
            dic={
                'a': {'str_value': 'limo', 'int_value': 10},
                'count': 10,
            },
            with_cls=B2,
            strict=True,
            exc=UnableFromDict,
            raises=dict(match='.*A2.*'),
        ),
        bad_case(
            name='panic if nested un-dictable when from_dict(.., strict)',
            obj=None,
            dic={
                'a': {'str_value': 'limo', 'int_value': 10, '@': 'A2'},
                'count': 10,
                '@': 'B2'
            },
            with_cls=None,
            strict=True,
            exc=UnableFromDict,
            raises=dict(match='.*A2.*'),
        ),
        bad_case(
            name='panic if wrapped un-dictable when to_dict(.., strict)',
            obj=B3(A(str_value='limo', int_value=10), count=20),
            dic=None,
            with_cls=True,
            strict=True,
            exc=UnableToDict,
            raises=dict(match='.*B3.*'),
        ),
        bad_case(
            name='panic if wrapped un-dictable when from_dict(.., strict, cls)',
            obj=None,
            dic={
                'a': {'str_value': 'limo', 'int_value': 10},
                'count': 10,
            },
            with_cls=B3,
            strict=True,
            exc=UnableFromDict,
            raises=dict(match='.*B3.*'),
        ),
        bad_case(
            name='panic if wrapped un-dictable when from_dict(.., strict)',
            obj=None,
            dic={
                'a': {'str_value': 'limo', 'int_value': 10, '@': 'A'},
                'count': 10,
                '@': 'B3'
            },
            with_cls=None,
            strict=True,
            exc=UnableFromDict,
            raises=dict(match='.*B3.*'),
        ),
    ]


def case_name(case):
    return case.name


class TestAnnotate:
    @pytest.mark.parametrize('case', generate_good_cases(), ids=case_name)
    def test_to_dict(self, case: good_case):
        assert AutoDict.to_dict(case.obj, with_cls=case.with_cls,
                                strict=case.strict) == case.dic

    @pytest.mark.parametrize('case', generate_good_cases(), ids=case_name)
    def test_from_dict(self, case: good_case):
        cls = None if case.with_cls else type(case.obj)
        output_obj = AutoDict.from_dict(case.dic, cls=cls, strict=case.strict)
        assert output_obj == case.obj

    @pytest.mark.parametrize('case', generate_bad_cases(), ids=case_name)
    def test_failed_to_or_from_dict(self, case: bad_case):
        with pytest.raises(case.exc, **case.raises):
            if case.dic is None:
                AutoDict.to_dict(case.obj, case.with_cls, strict=case.strict)
            elif case.obj is None:
                AutoDict.from_dict(case.dic, case.with_cls, strict=case.strict)

    @to_dictable
    class F:
        def __init__(self, str_value, int_value):
            self.str_value = str_value
            self.int_value = int_value

    def test_to_dictable_to_dict(self):
        f = TestAnnotate.F(str_value='limo', int_value=10)
        dict_f = AutoDict.to_dict(f)

        assert dict_f == {'str_value': 'limo', 'int_value': 10, '@': 'F'}

    def test_to_dictable_from_dict(self):
        dict_f = {'str_value': 'limo', 'int_value': 10, '@': 'F'}

        with pytest.raises(UnableFromDict, match='.*F.*'):
            AutoDict.from_dict(dict_f)

    @from_dictable
    class G:
        def __init__(self, str_value, int_value):
            self.str_value = str_value
            self.int_value = int_value

        def __eq__(self, other):
            return isinstance(other, TestAnnotate.G) and \
                self.str_value == other.str_value and \
                self.int_value == other.int_value

    def test_from_dictable_from_dict(self):
        dict_g = {'str_value': 'limo', 'int_value': 10, '@': 'G'}

        g = AutoDict.from_dict(dict_g, TestAnnotate.G)
        assert g == TestAnnotate.G(str_value='limo', int_value=10)

    def test_from_dictable_to_dict(self):
        g = TestAnnotate.G(str_value='limo', int_value=10)

        with pytest.raises(UnableToDict, match='.*G.*'):
            AutoDict.to_dict(g)

    @to_dictable
    @from_dictable
    class H:
        def __init__(self, str_value, int_value):
            self.str_value = str_value
            self.int_value = int_value

        def __eq__(self, other):
            return isinstance(other, TestAnnotate.H) and \
                self.str_value == other.str_value and \
                self.int_value == other.int_value

    def test_to_from_dictable(self):
        h = TestAnnotate.H(str_value='limo', int_value=10)
        dict_h = AutoDict.to_dict(h)

        assert dict_h == {'str_value': 'limo', 'int_value': 10, '@': 'H'}
        output_h = AutoDict.from_dict(dict_h)
        assert h == output_h


class TestDerive:
    class F(Dictable):
        def __init__(self, str_value, int_value):
            self.str_value = str_value
            self.int_value = int_value

        def __eq__(self, other):
            return isinstance(other, TestDerive.F) and \
                self.str_value == other.str_value and \
                self.int_value == other.int_value

    def test_derive_without_overwritten(self):
        f = TestDerive.F(str_value='limo', int_value=10)

        dict_f = AutoDict.to_dict(f)
        assert dict_f == {
            'str_value': 'limo', 'int_value': 10, '@': 'F'
        }

        output_f = AutoDict.from_dict(dict_f, TestDerive.F)
        assert f == output_f

    class F1(Dictable, name='SomeF'):
        def __init__(self, str_value, int_value):
            self.str_value = str_value
            self.int_value = int_value

        def __eq__(self, other):
            return isinstance(other, TestDerive.F) and \
                self.str_value == other.str_value and \
                self.int_value == other.int_value

    def test_derive_without_overwritten_but_customized_name(self):
        f = TestDerive.F1(str_value='limo', int_value=10)

        dict_f = AutoDict.to_dict(f)
        assert dict_f == {
            'str_value': 'limo', 'int_value': 10, '@': 'SomeF'
        }

        output_f = AutoDict.from_dict(dict_f, TestDerive.F)
        assert f == output_f

    class G(Dictable):
        def __init__(self):
            self.str_value = ''
            self.int_value = 0

        def __eq__(self, other):
            return isinstance(other, TestDerive.G) and \
                self.str_value == other.str_value and \
                self.int_value == other.int_value

        @classmethod
        def _from_dict(cls, dic: dict) -> 'TestDerive.G':
            g = TestDerive.G()
            g.str_value = dic['str_value']
            g.int_value = dic['int_value']
            return g

        def _to_dict(self) -> dict:
            return {
                'str_value': self.str_value,
                'int_value': self.int_value
            }

    def test_derive_with_overwritten(self):
        g = TestDerive.G()
        g.str_value = 'limo'
        g.int_value = 10

        dict_g = AutoDict.to_dict(g)
        assert dict_g == {
            'str_value': 'limo', 'int_value': 10, '@': 'G'
        }

        output_g = AutoDict.from_dict(dict_g, TestDerive.G)
        assert g == output_g

    class H(Dictable):
        g: 'TestDerive.G'

        def __init__(self):
            self.g = TestDerive.G()
            self.count = 0

        def __eq__(self, other):
            return self.g == other.g and \
                self.count == other.count

        @classmethod
        def _from_dict(cls, dic: dict) -> 'TestDerive.H':
            h = TestDerive.H()
            h.g = dic['g']
            h.count = dic['count']
            return h

        def _to_dict(self) -> dict:
            return {
                'g': self.g,
                'count': self.count
            }

    def test_nested_derive_with_overwritten(self):
        h = TestDerive.H()
        h.g = TestDerive.G()
        h.g.str_value = 'limo'
        h.g.int_value = 10
        h.count = 20

        dict_h = AutoDict.to_dict(h)
        assert dict_h == {
            'g': {'str_value': 'limo', 'int_value': 10, '@': 'G'},
            'count': 20,
            '@': 'H'
        }

        output_h = AutoDict.from_dict(dict_h, TestDerive.H)
        assert h == output_h
