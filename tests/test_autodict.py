import enum
import pathlib
from typing import List

import pytest

from autodict import dictable, AutoDict
from autodict.autodict import Dictable, UnableToDict, UnableFromDict, \
    to_dictable, from_dictable


@dictable
class A:
    def __init__(self, str_value, int_value):
        self.str_value = str_value
        self.int_value = int_value

    def __eq__(self, other):
        return self.str_value == other.str_value and \
            self.int_value == other.int_value

    def __str__(self):
        return f'({self.str_value}, {self.int_value})'


class A2:
    def __init__(self, str_value, int_value):
        self.str_value = str_value
        self.int_value = int_value


@dictable
class A3:
    def __init__(self):
        self._protected_value = ''
        self.__private_value = 0

    def set(self, protected_value, private_value):
        self._protected_value = protected_value
        self.__private_value = private_value

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
class Color(enum.Enum):
    Black = 1
    Red = 2


class TestAnnotate:
    def test_to_dict(self):
        a = A(str_value='limo', int_value=10)
        assert AutoDict.to_dict(a) == {
            'str_value': 'limo', 'int_value': 10, '@': 'A'
        }
        assert AutoDict.to_dict(a, with_cls=False) == {
            'str_value': 'limo', 'int_value': 10
        }

    def test_from_dict_with_embedded_cls(self):
        a = A(str_value='limo', int_value=10)

        dict_a = AutoDict.to_dict(a)
        output_a = AutoDict.from_dict(dict_a)
        assert a == output_a

    def test_from_dict_with_explicit_cls(self):
        a = A(str_value='limo', int_value=10)

        dict_a = AutoDict.to_dict(a, with_cls=False)
        output_a = AutoDict.from_dict(dict_a, A)
        assert a == output_a

    def test_from_dict_without_anything(self):
        a = A(str_value='limo', int_value=10)

        dict_a = AutoDict.to_dict(a, with_cls=False)
        output_a = AutoDict.from_dict(dict_a)
        assert dict_a == output_a

    def test_force_to_dict(self):
        a = A2(str_value='limo', int_value=10)

        with pytest.raises(UnableToDict, match='.*A2.*'):
            AutoDict.to_dict(a)

    def test_allow_unable_to_dict(self):
        a = A2(str_value='limo', int_value=10)

        failed_dict_a = AutoDict.to_dict(a, strict=False)
        assert a == failed_dict_a

    def test_force_from_dict(self):
        dict_a = {'str_value': 'limo', 'int_value': 10}

        with pytest.raises(UnableFromDict, match='.*A2.*'):
            AutoDict.from_dict(dict_a, A2)

    def test_allow_unable_from_dict(self):
        dict_a = {'str_value': 'limo', 'int_value': 10}

        failed_a = AutoDict.from_dict(dict_a, A2, strict=False)
        assert dict_a == failed_a

    def test_to_dict_with_hidden_fields_without_constructor_args(self):
        a = A3()
        a.set('name', 10)
        dict_a = AutoDict.to_dict(a)

        assert dict_a == {
            '_protected_value': 'name',
            '_A3__private_value': 10,
            '@': 'A3'
        }

        output_a = AutoDict.from_dict(dict_a)
        assert a == output_a

    def test_to_dict_with_hidden_fields_with_constructor_args(self):
        a = A4('name', 10)
        dict_a = AutoDict.to_dict(a)

        assert dict_a == {
            '_protected_value': 'name',
            '_A4__private_value': 10,
            '@': 'A4'
        }

        output_a = AutoDict.from_dict(dict_a)
        assert a == output_a
    
    def test_to_dict_with_inherited_hidden_fields_with_constructor_args(self):
        a = A5('name', 10)
        dict_a = AutoDict.to_dict(a)

        assert dict_a == {
            '_protected_value': 'name',
            '_A4__private_value': 10,
            '@': 'A5'
        }
 
        output_a = AutoDict.from_dict(dict_a)
        assert a == output_a

    @dictable
    class B:
        a: A

        def __init__(self, a, count):
            self.a = a
            self.count = count

        def __eq__(self, other):
            return self.a == other.a and self.count == other.count

    def test_nested_to_dict(self):
        a = A(str_value='limo', int_value=10)
        b = TestAnnotate.B(a=a, count=20)

        assert AutoDict.to_dict(b) == {
            'a': {'str_value': 'limo', 'int_value': 10, '@': 'A'},
            'count': 20,
            '@': 'B'
        }
        assert AutoDict.to_dict(b, with_cls=False) == {
            'a': {'str_value': 'limo', 'int_value': 10},
            'count': 20,
        }
        assert AutoDict.to_dict(b, recursively=False) == {
            'a': a,
            'count': 20,
            '@': 'B'
        }

    def test_nested_from_dict_with_embedded_cls(self):
        a = A(str_value='limo', int_value=10)
        b = TestAnnotate.B(a=a, count=20)

        dict_b = AutoDict.to_dict(b)
        output_b = AutoDict.from_dict(dict_b)
        assert b == output_b

    @dictable
    class B2:
        a: A2

        def __init__(self, a, count):
            self.a = a
            self.count = count

        def __eq__(self, other):
            return self.a == other.a and self.count == other.count

    def test_nested_force_to_dict(self):
        a = A2(str_value='limo', int_value=10)
        b = TestAnnotate.B2(a=a, count=20)

        with pytest.raises(UnableToDict, match='.*A2.*'):
            AutoDict.to_dict(b)

    def test_nested_allow_unable_to_dict(self):
        a = A2(str_value='limo', int_value=10)
        b = TestAnnotate.B2(a=a, count=20)

        failed_dict_b = AutoDict.to_dict(b, strict=False)
        assert {'a': a, 'count': 20, '@': 'B2'} == failed_dict_b

    def test_nested_force_from_dict(self):
        dict_b = {
            'a': {'str_value': 'limo', 'int_value': 10, '@': 'A2'},
            'count': 10,
            '@': 'B2'
        }

        with pytest.raises(UnableFromDict, match='.*A2.*'):
            AutoDict.from_dict(dict_b, TestAnnotate.B2)

    def test_nested_allow_unable_from_dict(self):
        dict_b = {
            'a': {'str_value': 'limo', 'int_value': 10, '@': 'A2'},
            'count': 10,
            '@': 'B2'
        }

        failed_b = AutoDict.from_dict(dict_b, TestAnnotate.B2, strict=False)
        assert TestAnnotate.B(a=dict_b['a'], count=10) == failed_b

    class B3:
        a: A

        def __init__(self, a, count):
            self.a = a
            self.count = count

        def __eq__(self, other):
            return isinstance(other, TestAnnotate.B3) and \
                self.a == other.a and \
                self.count == other.count

    def test_outer_force_to_dict(self):
        a = A(str_value='limo', int_value=10)
        b = TestAnnotate.B3(a=a, count=20)

        with pytest.raises(UnableToDict, match='.*B3.*'):
            AutoDict.to_dict(b)

    def test_outer_allow_unable_to_dict(self):
        a = A(str_value='limo', int_value=10)
        b = TestAnnotate.B3(a=a, count=20)

        # if a class is un-to_dictable, then its field will not be transformed
        failed_dict_b = AutoDict.to_dict(b, strict=False)
        assert b == failed_dict_b

    def test_outer_force_from_dict(self):
        dict_b = {
            'a': {'str_value': 'limo', 'int_value': 10, '@': 'A'},
            'count': 20,
            '@': 'B3'
        }

        with pytest.raises(UnableFromDict, match='.*B3.*'):
            AutoDict.from_dict(dict_b, TestAnnotate.B3)

    def test_outer_allow_unable_from_dict(self):
        dict_b = {
            'a': {'str_value': 'limo', 'int_value': 10, '@': 'A'},
            'count': 20,
        }

        # if a class is un-from_dictable, its fields will still be transformed
        failed_b = AutoDict.from_dict(dict_b, TestAnnotate.B3, strict=False)
        assert {'a': A(str_value='limo', int_value=10), 'count': 20} == failed_b

    @dictable
    class C:
        a: A

        def __init__(self, a, count):
            self.a = a
            self.count = count

        def __eq__(self, other):
            return self.a == other.a and self.count == other.count

    def test_nested_from_dict_with_annotation_cls(self):
        a = A(str_value='limo', int_value=10)
        c = TestAnnotate.C(a=a, count=20)

        dict_c = AutoDict.to_dict(c, with_cls=False)
        output_c = AutoDict.from_dict(dict_c, TestAnnotate.C)
        assert c == output_c

    @dictable
    class C2:
        b: 'TestAnnotate.B'
        b_list: List['TestAnnotate.B']

        def __init__(self, b, b_list, count):
            self.b = b
            self.b_list = b_list
            self.count = count

        def __eq__(self, other):
            return self.b == other.b and \
                self.b_list == other.b_list and \
                self.count == other.count

    def test_nested_from_dict_with_annotation_str_cls(self):
        a = A(str_value='limo', int_value=10)
        b = TestAnnotate.B(a, count=10)
        c = TestAnnotate.C2(b, [b], count=20)

        dict_c = AutoDict.to_dict(c)
        assert isinstance(dict_c, dict)

        output_c = AutoDict.from_dict(dict_c, TestAnnotate.C2)
        assert c == output_c

    @dictable
    class D:
        a_list: List[A]

        def __init__(self, a_list, count):
            self.a_list = a_list
            self.count = count

        def __eq__(self, other):
            return self.a_list == other.a_list and self.count == other.count

    def test_nested_from_dict_with_generic_cls(self):
        a = A(str_value='limo', int_value=10)
        d = TestAnnotate.D(a_list=[a], count=20)

        dict_d = AutoDict.to_dict(d, with_cls=False)
        output_d = AutoDict.from_dict(dict_d, TestAnnotate.D)
        assert d == output_d

    @dictable
    class E:
        path: pathlib.Path
        color: Color

        def __init__(self, path, color):
            self.path = path
            self.color = color

        def __eq__(self, other):
            return self.path == other.path and self.color == other.color

    def test_special_types(self):
        e = TestAnnotate.E(path=pathlib.Path('/home/limo/.bashrc'),
                           color=Color.Red)
        dict_e = AutoDict.to_dict(e)
        assert isinstance(dict_e, dict)
        output_e = AutoDict.from_dict(dict_e, TestAnnotate.E)
        assert e == output_e

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

    def test_from_dictable_from_dict(self):
        dict_g = {'str_value': 'limo', 'int_value': 10, '@': 'G'}

        g = AutoDict.from_dict(dict_g, TestDerive.G)
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
            return self.str_value == other.str_value and \
                self.int_value == other.int_value

    def test_derive_without_overwritten(self):
        f = TestDerive.F(str_value='limo', int_value=10)

        dict_f = AutoDict.to_dict(f)
        assert dict_f == {
            'str_value': 'limo', 'int_value': 10, '@': 'F'
        }

        output_f = AutoDict.from_dict(dict_f, TestDerive.F)
        assert f == output_f

    class G(Dictable):
        def __init__(self):
            self.str_value = ''
            self.int_value = 0

        def __eq__(self, other):
            return self.str_value == other.str_value and \
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
