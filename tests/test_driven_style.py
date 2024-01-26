from autodict import AutoDict, Dictable, Options


class TestDerive:
    class General(Dictable):
        def __init__(self, str_value, int_value):
            self.str_value = str_value
            self.int_value = int_value

        def __eq__(self, other):
            return (
                isinstance(other, TestDerive.General)
                and self.str_value == other.str_value
                and self.int_value == other.int_value
            )

    def test_derive_without_overwritten(self):
        f = TestDerive.General(str_value="limo", int_value=10)

        dict_f = AutoDict.to_dict(f)
        assert dict_f == {"str_value": "limo", "int_value": 10, "@": "General"}

        output_f = AutoDict.from_dict(dict_f, TestDerive.General)
        assert f == output_f

    class CustomName(Dictable, name="SomeF"):
        def __init__(self, str_value, int_value):
            self.str_value = str_value
            self.int_value = int_value

        def __eq__(self, other):
            return (
                isinstance(other, TestDerive.CustomName)
                and self.str_value == other.str_value
                and self.int_value == other.int_value
            )

    def test_derive_without_overwritten_but_customized_name(self):
        f = TestDerive.CustomName(str_value="limo", int_value=10)

        dict_f = AutoDict.to_dict(f)
        assert dict_f == {"str_value": "limo", "int_value": 10, "@": "SomeF"}

        output_f = AutoDict.from_dict(dict_f, TestDerive.General)
        assert f == output_f

    class OverrideBoth(Dictable):
        def __init__(self):
            self.str_value = ""
            self.int_value = 0

        def __eq__(self, other):
            return (
                isinstance(other, TestDerive.OverrideBoth)
                and self.str_value == other.str_value
                and self.int_value == other.int_value
            )

        @classmethod
        def _from_dict(cls, obj: dict, _: Options) -> "TestDerive.OverrideBoth":
            g = TestDerive.OverrideBoth()
            g.str_value = obj["str_value"]
            g.int_value = obj["int_value"]
            return g

        def _to_dict(self, _: Options) -> dict:
            return {"str_value": self.str_value, "int_value": self.int_value}

    def test_derive_with_overwritten(self):
        g = TestDerive.OverrideBoth()
        g.str_value = "limo"
        g.int_value = 10

        dict_g = AutoDict.to_dict(g)
        assert dict_g == {"str_value": "limo", "int_value": 10, "@": "OverrideBoth"}

        output_g = AutoDict.from_dict(dict_g, TestDerive.OverrideBoth)
        assert g == output_g

    class NestedOverride(Dictable):
        g: "TestDerive.OverrideBoth"

        def __init__(self):
            self.g = TestDerive.OverrideBoth()
            self.count = 0

        def __eq__(self, other):
            return self.g == other.g and self.count == other.count

        @classmethod
        def _from_dict(cls, obj: dict, _) -> "TestDerive.NestedOverride":
            h = TestDerive.NestedOverride()
            h.g = obj["g"]
            h.count = obj["count"]
            return h

        def _to_dict(self, _: Options) -> dict:
            return {"g": self.g, "count": self.count}

    def test_nested_derive_with_overwritten(self):
        h = TestDerive.NestedOverride()
        h.g = TestDerive.OverrideBoth()
        h.g.str_value = "limo"
        h.g.int_value = 10
        h.count = 20

        dict_h = AutoDict.to_dict(h)
        assert dict_h == {
            "g": {"str_value": "limo", "int_value": 10, "@": "OverrideBoth"},
            "count": 20,
            "@": "NestedOverride",
        }

        output_h = AutoDict.from_dict(dict_h, TestDerive.NestedOverride)
        assert h == output_h
