# AutoDict

[![AutoDict unit tests](https://github.com/limoiie/autodict/actions/workflows/python-package.yml/badge.svg?branch=master)](https://github.com/limoiie/autodict/actions?branch=master)
[![Codacy Badge](https://app.codacy.com/project/badge/Grade/5842f736f8404c1ababfd439b5eeea05)](https://www.codacy.com/gh/limoiie/autodict/dashboard?utm_source=github.com&amp;utm_medium=referral&amp;utm_content=limoiie/autodict&amp;utm_campaign=Badge_Grade)

AutoDict is a package that converts Python objects to and from dictionaries, 
containing only built-in Python objects.

One use case of AutoDict is to support automatic serialization and deserialization,
such as JSON or YAML, for Python objects by converting them to/from dictionaries.

## Get started

### Install from source code

Run the following command in a shell:

```shell
python -m pip install git+https://github.com/limoiie/autodict.git@v0.0.4
```

### Introduction

Here's a simple example:

```python
import json
from autodict import dictable, AutoDict

@dictable
class Student:
    def __init__(self, name, age):
        self.name = name
        self.age = age

    def __eq__(self, other):
        return (
            isinstance(other, Student)
            and self.name == other.name and self.age == other.age
        )

student = Student('limo', 90)
student_dict = AutoDict.to_dict(student)
json_string = json.dumps(student_dict)
with open(..., 'w+') as f:
    f.write(json_string)

recovered_student = AutoDict.from_dict(student_dict)
assert student == recovered_student
```

In the code above, 
we annotate the custom class as `dictable` using the `dictable` annotator.
After marking it, you can use `AutoDict.to_dict` and `AutoDict.from_dict` 
to convert between objects and dictionaries.

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
```

### Mark in derive style

Or, you can derive from the `AutoDictable` base class:

```python
from autodict import Dictable

class Student(Dictable):
    def __init__(self, name, age):
        self.name = name
        self.age = age
```

### Mark nested dictable

To support auto-dict recursively, you need to provide field types in class annotations.

```python
from typing import List
from autodict import dictable

@dictable
class Student:
    ...

@dictable
class Apartment:
    students: List[Student]

    def __init__(self, students):
        self.students = students
```

### Support dataclasses, namedtuples, and enum subclasses out of box

AutoDict supports dataclasses, namedtuples, and enum subclasses out of box.

```python
from dataclasses import dataclass
from enum import Enum
from typing import NamedTuple

from autodict import AutoDict

class Apartment(NamedTuple):
    address: str

class Gender(Enum):
    MAN = 0
    WOMAN = 1
    OTHERS = 2

@dataclass
class Student:
    name: str
    age: int
    apartment: Apartment
    gender: Gender
    
student = Student(
    name="limo",
    age=70,
    apartment=Apartment(
        address="Solar System",
    ),
    gender=Gender.OTHERS,
)

student_dict = AutoDict.to_dict(student)
assert student == {
    "name": "limo",
    "age": 70,
    "apartment": {
        "address": "Solar System",
        "@": "Apartment",
    },
    "gender": {
        "name": "OTHERS",
        "value": 2,
        "@": "Gender"
    },
    "@": "Student",
}

o_student = AutoDict.from_dict(student_dict)
assert student == o_student
```

### Transform with embedded class info

During the transformation from object to dictionary,
you can embed the class name into the output dictionary,
so that no explicit type is required for the reverse transformation.

```python
from autodict import AutoDict, Dictable, Options

class Student(Dictable):
    def __init__(self, name, age):
        self.name = name
        self.age = age

student = Student('limo', 90)
# tell the to_dict function to embed the class name into the output dictionary
student_dict = AutoDict.to_dict(student, options=Options(with_cls=True))
o_student = AutoDict.from_dict(student_dict)
assert student == o_student
```

### Transform with explicit type

Alternatively,
you can strip out the class information from the output dictionary to make it clean.
In this case, when you transform the dictionary back to the object,
you need to provide the type explicitly:

```python
from autodict import AutoDict, Dictable, Options

class Student(Dictable):
    def __init__(self, name, age):
        self.name = name
        self.age = age

student = Student('limo', 90)
# tell the to_dict function not to embed the class name into the output dictionary
student_dict = AutoDict.to_dict(student, options=Options(with_cls=False))
# explicitly provide the from_dict function the type of the object
o_student = AutoDict.from_dict(student_dict, cls=Student)
assert student == o_student
```

### Deal with private fields

Protected and private fields are also supported. 
Before trying to instantiate the class with the constructor,
the trivial prefix will be stripped out of keys of the dictionary, as shown below:

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

When a class has a private field, 
the key for that field in the `__dict__` would be prefixed with `_{cls.__name__}`.
That's why the key for `Student.__age` in the output dictionary 
is prefixed with '_Student'.

### Overwrite default transformation behavior

The default `to_dict` reads objects' field `__dict__` 
to generate the dictionary structure.

On the other hand, the default `from_dict` first tries to call the class constructor 
without any arguments, 
and then assigns the dictionary to the object's field `__dict__`. 
If that fails,
the default `from_dict` will call the class constructor 
with the dictionary as the kwargs.

To overwrite the behavior in annotator style,
you need to provide the transform functions in the annotator's call interface:

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

To overwrite in derive style, just override the methods `_to_dict` and `_from_dict`:

```python
from autodict import Dictable, Options

class Student(Dictable):
    def __init__(self, name_age):
        self.name, self.age = name_age.rsplit('.', maxsplit=1)

    def _to_dict(self, options: Options) -> dict:
        return {
            'name-age': f'{self.name}.{self.age}'
        }

    @classmethod
    def _from_dict(cls, dic: dict, options: Options) -> 'Student':
        return Student(dic['name-age'])
```

### Partially dictable in annotator style

If you only want the `to_dict` or the `from_dict` functionality, 
you can annotate with `to_dictable` or `from_dictable`:

```python
from autodict import to_dictable, AutoDict

@to_dictable
class Student:
    def __init__(self, name, age):
        self.name = name
        self.age = age

student = Student(name='limo', age=90)
student_dict = AutoDict.to_dict(student)
AutoDict.from_dict(student_dict)  # throws exception UnableFromDict
```

### Partially dictable in derive style

If you derive `Dictable`, 
you can achieve partial dictability by calling the function `unable_*_dict` explicitly:

```python
from autodict import AutoDict, Dictable, Options
from autodict.predefined import unable_from_dict

class Student(Dictable):
    def __init__(self, name, age):
        self.name = name
        self.age = age

    @classmethod
    def _from_dict(cls, dic: dict, options: Options):
        return unable_from_dict(cls, dic, options)

student = Student(name='limo', age=90)
student_dict = AutoDict.to_dict(student)
AutoDict.from_dict(student_dict)  # throws exception UnableFromDict
```
