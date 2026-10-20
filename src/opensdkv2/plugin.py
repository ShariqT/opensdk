from typing import Protocol

class Plugin(Protocol):
    def validate_spec(filepath: str):
        raise NotImplementedError

    def return_prompt() -> str:
        raise NotImplementedError

