from dataclasses import is_dataclass, fields
from enum import Enum, Flag
from typing import Any


class CopyTools:
    @staticmethod
    def full_copy(obj: Any) -> Any:
        if isinstance(obj, (int, float, str, bool, type(None), Enum, Flag)):
            return obj
        elif isinstance(obj, list):
            return [CopyTools.full_copy(item) for item in obj]
        elif isinstance(obj, tuple):
            return tuple(CopyTools.full_copy(item) for item in obj)
        elif isinstance(obj, set):
            return {CopyTools.full_copy(item) for item in obj}
        elif isinstance(obj, dict):
            return {CopyTools.full_copy(k): CopyTools.full_copy(v) for k, v in obj.items()}
        elif is_dataclass(obj):
            cls = type(obj)
            kwargs = {}
            for f in fields(obj):
                value = getattr(obj, f.name)
                kwargs[f.name] = CopyTools.full_copy(value)
            return cls(**kwargs)
        else:
            raise TypeError(f"Unsupported type for full_copy: {type(obj)}")