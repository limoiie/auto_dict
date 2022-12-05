from typing import Optional


class UnableToDict(Exception):
    def __init__(self, cls: Optional[type]):
        super().__init__(
            f'{cls}, please mark it as to_dictable.')


class UnableFromDict(Exception):
    def __init__(self, cls: Optional[type]):
        super().__init__(
            f'{cls}, please mark it as from_dictable.')
