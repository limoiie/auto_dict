import pytest

from autodict import AutoDict, from_dictable, to_dictable
from autodict.errors import UnableFromDict, UnableToDict


class TestAnnotatePartially:
    @to_dictable
    class PartialTo:
        def __init__(self, str_value, int_value):
            self.str_value = str_value
            self.int_value = int_value

    def test_to_dictable_to_dict(self):
        f = TestAnnotatePartially.PartialTo(str_value="limo", int_value=10)
        dict_f = AutoDict.to_dict(f)

        assert dict_f == {"str_value": "limo", "int_value": 10, "@": "PartialTo"}

    def test_to_dictable_from_dict(self):
        dict_f = {"str_value": "limo", "int_value": 10, "@": "PartialTo"}

        with pytest.raises(UnableFromDict, match=".*PartialTo.*"):
            AutoDict.from_dict(dict_f)

    @from_dictable
    class PartialFrom:
        def __init__(self, str_value, int_value):
            self.str_value = str_value
            self.int_value = int_value

        def __eq__(self, other):
            return (
                isinstance(other, TestAnnotatePartially.PartialFrom)
                and self.str_value == other.str_value
                and self.int_value == other.int_value
            )

    def test_from_dictable_from_dict(self):
        dict_g = {"str_value": "limo", "int_value": 10, "@": "PartialFrom"}

        g = AutoDict.from_dict(dict_g, TestAnnotatePartially.PartialFrom)
        assert g == TestAnnotatePartially.PartialFrom(str_value="limo", int_value=10)

    def test_from_dictable_to_dict(self):
        g = TestAnnotatePartially.PartialFrom(str_value="limo", int_value=10)

        with pytest.raises(UnableToDict, match=".*PartialFrom.*"):
            AutoDict.to_dict(g)

    @to_dictable
    @from_dictable
    class PartialBoth:
        def __init__(self, str_value, int_value):
            self.str_value = str_value
            self.int_value = int_value

        def __eq__(self, other):
            return (
                isinstance(other, TestAnnotatePartially.PartialBoth)
                and self.str_value == other.str_value
                and self.int_value == other.int_value
            )

    def test_to_from_dictable(self):
        h = TestAnnotatePartially.PartialBoth(str_value="limo", int_value=10)
        dict_h = AutoDict.to_dict(h)

        assert dict_h == {"str_value": "limo", "int_value": 10, "@": "PartialBoth"}
        output_h = AutoDict.from_dict(dict_h)
        assert h == output_h
