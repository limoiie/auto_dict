from typing import Optional


class AutoDictError(Exception):
    def __init__(self, msg):
        self.msg = msg

    def __str__(self):
        return self.msg


class UnableToDict(AutoDictError):
    def __init__(self, cls: Optional[type]):
        super().__init__(f"{cls}, please mark it as to_dictable.")


class UnableFromDict(AutoDictError):
    def __init__(self, cls: Optional[type]):
        super().__init__(f"{cls}, please mark it as from_dictable.")
