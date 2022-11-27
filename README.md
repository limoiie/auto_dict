# Auto Dict

[![AutoDict unit tests](https://github.com/limoiie/autodict/actions/workflows/python-package.yml/badge.svg?branch=master)](https://github.com/limoiie/autodict/actions?branch=master)
[![Codacy Badge](https://app.codacy.com/project/badge/Grade/5842f736f8404c1ababfd439b5eeea05)](https://www.codacy.com/gh/limoiie/autodict/dashboard?utm_source=github.com&amp;utm_medium=referral&amp;utm_content=limoiie/autodict&amp;utm_campaign=Badge_Grade)

AutoDict is a package for transforming between python objects and dicts, where
the dicts contain only python builtin objects.

A use case of `AutoDict` will be converting python objects to/from dict to
automatically support any kinds of serialization/deserialization, such as json
or yaml.

## Get started

### Install from source code

Run in the shell:

```shell
python -m pip install git+https://github.com/limoiie/autodict.git@v0.0.3
```

### Introduction

A simple example may be like:

```python
import json

from autodict import dictable, AutoDict


@dictable
class Student:
    def __init__(self, name, age):
        self.name = name
        self.age = age

    # for comparison
    def __eq__(self, other):
        return isinstance(other, Student) and \
            self.name == other.name and \
            self.age == other.age


# convert object to dict
student = Student('limo', 90)
student_dict = AutoDict.to_dict(student)

# if you want to serialize the object, just dump the dict
json_string = json.dumps(student_dict)
with open(..., 'w+') as f:
    f.write(json_string)

# convert dict back to object
recovered_student = AutoDict.from_dict(student_dict)
assert student == recovered_student
```

In the above code, we first mark the custom class as dictable by using
the `dictable` annotator. Once marked, you can call `AutoDict.to_dict` and
`AutoDict.from_dict` to transform between objects and dictionaries.

## Usages

### Mark in annotator style

`AutoDict` provides two ways to mark a custom class as dictable.

You can annotate your class as dictable:

```python
from autodict import dictable


@dictable
class Student:
    def __init__(self, name, age):
        self.name = name
        self.age = age

    ...
```

### Mark in derive style

Or, you can derive from the `AutoDictable` base class:

```python
from autodict import Dictable


class Student(Dictable):
    def __init__(self, name, age):
        self.name = name
        self.age = age

    ...
```

### Mark nested dictable

To support auto-dict recursively, you need provide field types in class
annotations.

```python
from typing import List

from autodict import dictable, Dictable


class Student(Dictable):
    ...


@dictable
class Apartment:
    students: List[Student]

    def __init__(self, students):
        self.students = students
```

### Transform with embedded class info

During the transforming from object to dictionary, you can embed the
class name into the output dictionary, so that no explicit type required for the
reverse transformation.

```python
from autodict import AutoDict, Dictable


class Student(Dictable):
    def __init__(self, name, age):
        self.name = name
        self.age = age

    ...


student = Student('limo', 90)
student_dict = AutoDict.to_dict(student)
o_student = AutoDict.from_dict(student_dict)
assert student == o_student
```

### Transform with explicit type

Or, you can strip out the class information from the output dictionary to make
it clean. In this case, when you transform from the dictionary back to the
object, you need to provide the type explicitly:

```python
from autodict import AutoDict, Dictable


class Student(Dictable):
    def __init__(self, name, age):
        self.name = name
        self.age = age

    ...


student = Student('limo', 90)
student_dict = AutoDict.to_dict(student, with_cls=False)
o_student = AutoDict.from_dict(student_dict, cls=Student)
assert student == o_student
```

### Deal with private fields

Protected and private fields are also supported. Before trying to instantiate
the class with constructor, the trivial prefix will be striped out of keys of
dict, as shown as:

```python
from autodict import AutoDict, Dictable


class Student(Dictable):
    def __init__(self, name, age):
        self._name = name
        self.__age = age

    def __eq__(self, other): ...


student = Student(name='limo', age=90)
student_dict = AutoDict.to_dict(student)
assert student_dict == {'_name': 'limo', '_Student__age': 90, '@': 'Student'}

output_student = AutoDict.from_dict(student_dict)
assert student == output_student
```

When a class has a private field, the key for that field in the `__dict__` would
be prefixed with `_{cls.__name__}`. That's why the key for `Student.__age` in
the output dict is prefixed with '_Student'.

### Overwrite default transformation behavior

The default to_dict reads objects' field `__dict__` to generate dict structure.

On the other side, the default from_dict first tries to call class constructor
without any arg, and then assign the dictionary to the object's field
`__dict__`. If that failed, the default from_dict will call the class
constructor with the dictionary as the kwargs.

To overwrite the behavior in annotator style, you need to provide the transform
functions in the annotator's call interface:

```python
from autodict import dictable


def student_to_dict(student):
    return {
        'name-age': f'{student.name}.{student.age}'
    }


def student_from_dict(dic, cls):
    assert cls is Student
    return cls(dic['name-age'])


@dictable(to_dict=student_to_dict, from_dict=student_from_dict)
class Student:
    def __init__(self, name_age):
        self.name, self.age = name_age.rsplit('.', maxsplit=1)
```

As for overwriting in derive style, just override methods `_to_dict` and
`_from_dict`:

```python
from autodict import Dictable


class Student(Dictable):
    def __init__(self, name_age):
        self.name, self.age = name_age.rsplit('.', maxsplit=1)

    def _to_dict(self) -> dict:
        return {
            'name-age': f'{self.name}.{self.age}'
        }

    @classmethod
    def _from_dict(cls, dic: dict) -> 'Student':
        return Student(dic['name-age'])
```

### Partially dictable in annotator style

If you only want the to_dict or the from_dict functionality, you can annotate
with `to_dictable` or `from_dictable`:

```python
from autodict import to_dictable, AutoDict


@to_dictable
class Student:
    def __init__(self, name, age):
        self.name = name
        self.age = age


student = Student(name='limo', age=90)
student_dict = AutoDict.to_dict(student)
AutoDict.from_dict(student_dict)  # throw exception UnableFromDict
```

### Partially dictable in derive style

If you derive `Dictable`, you can achieve partially dictable by calling function
`unable_*_dict` explicitly:

```python
from autodict import AutoDict, Dictable
from autodict.autodict import unable_from_dict


class Student(Dictable):
    def __init__(self, name, age):
        self.name = name
        self.age = age

    @classmethod
    def _from_dict(cls, dic: dict):
        return unable_from_dict(cls, dic)


student = Student(name='limo', age=90)
student_dict = AutoDict.to_dict(student)
AutoDict.from_dict(student_dict)  # throw exception UnableFromDict
```
