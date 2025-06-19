import json
from pydantic import BaseModel
from typing import Any, Dict, Optional

def debug_obj(obj: Any, label: str = "Object") -> str:
    """Generate a debug string representation of an object"""
    if isinstance(obj, BaseModel):
        return f"{label} ({type(obj).__name__}): {obj.model_dump_json(indent=2)}"
    elif isinstance(obj, dict):
        return f"{label} (dict): {json.dumps(obj, indent=2)}"
    else:
        return f"{label} ({type(obj).__name__}): {str(obj)}"

def save_debug_info(obj: Any, filename: str) -> None:
    """Save debug information to a file"""
    with open(filename, 'w') as f:
        if isinstance(obj, BaseModel):
            f.write(obj.model_dump_json(indent=2))
        elif isinstance(obj, dict):
            json.dump(obj, f, indent=2)
        else:
            f.write(str(obj))
