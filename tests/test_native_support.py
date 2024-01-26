import dataclasses
import enum
from collections import namedtuple
from typing import List

import pytest

from autodict import AutoDict, Options

GoodCase = namedtuple("GoodCase", "ins,obj,opts,name")

BadCase = namedtuple("BadCase", "ins,obj,cls,opts,exc,raises,name")


class Color(enum.Enum):
    Black = 1
    Red = 2


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


@dataclasses.dataclass
class DataclassWithEnumAndDataclassFields:
    value: NativeDataclass
    color: Color


def generate_good_cases():
    return [
        GoodCase(
            name="native dataclass",
            ins=NativeDataclass(str_value="limo", list_value=[10, 20]),
            obj={"str_value": "limo", "list_value": [10, 20]},
            opts=Options(with_cls=False, strict=True),
        ),
        GoodCase(
            name="native dataclass - autodict with class",
            ins=NativeDataclass("str_value", [1, 2, 3]),
            obj={
                "str_value": "str_value",
                "list_value": [1, 2, 3],
                "@": "NativeDataclass",
            },
            opts=Options(with_cls=True, strict=True),
        ),
        GoodCase(
            name="dataclass with fields",
            ins=DataclassWithField(init_value="A", init_variable=10, default_value=20),
            obj={"init_value": "A", "post_init_value": 30, "default_value": 20},
            opts=Options(with_cls=False, strict=True),
        ),
        GoodCase(
            name="dataclass with fields - autodict with class",
            ins=DataclassWithField(init_value="A", init_variable=10, default_value=20),
            obj={
                "init_value": "A",
                "post_init_value": 30,
                "default_value": 20,
                "@": "DataclassWithField",
            },
            opts=Options(with_cls=True, strict=True),
        ),
        GoodCase(
            name="dataclass with enum and dataclass fields",
            ins=DataclassWithEnumAndDataclassFields(
                NativeDataclass("str_value", [1, 2, 3]), Color.Black
            ),
            obj={
                "value": {"str_value": "str_value", "list_value": [1, 2, 3]},
                "color": {"name": "Black", "value": 1},
            },
            opts=Options(with_cls=False, strict=True),
        ),
        GoodCase(
            name="dataclass with enum and dataclass fields - autodict with class",
            ins=DataclassWithEnumAndDataclassFields(
                NativeDataclass("str_value", [1, 2, 3]), Color.Black
            ),
            obj={
                "value": {
                    "str_value": "str_value",
                    "list_value": [1, 2, 3],
                    "@": "NativeDataclass",
                },
                "color": {"name": "Black", "value": 1, "@": "Color"},
                "@": "DataclassWithEnumAndDataclassFields",
            },
            opts=Options(with_cls=True, strict=True),
        ),
    ]


def case_name(case):
    return case.name


class TestNativeSupport:
    """
    Test native support for dataclasses and enums.

    Currently, dataclasses and enums are supported natively.
    Autodict supports dataclasses and enums out of the box (natively).
    That is, given a dataclass or enum,
    autodict is able to serialize it to a dict and deserialize it from a dict
    without the need of registration or the inheritance of the base class.

    The downside of native support is that
    we cannot get the class of the dataclass or enum by only the name.
    One possible way to solve this problem is to scan the whole user side project
    to find the class with the same name.
    However, this is not a good idea because it is too slow and error-prone,
    therefore this feature is not implemented yet.
    So that, if dealing with dataclass or enum with only native support,
    the class must be specified explicitly to deserialize the dict.
    """

    @pytest.mark.parametrize("case", generate_good_cases(), ids=case_name)
    def test_to_dict(self, case: GoodCase):
        assert AutoDict.to_dict(case.ins, case.opts) == case.obj

    @pytest.mark.parametrize("case", generate_good_cases(), ids=case_name)
    def test_from_dict(self, case: GoodCase):
        cls = type(case.ins)  # need specify the class explicitly
        output_obj = AutoDict.from_dict(case.obj, cls, case.opts)
        assert output_obj == case.ins
