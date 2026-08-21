import json
import re
from typing import Any, Union
import json_repair
from pydantic import BaseModel


def sanitize_json_string(raw_json: str) -> str:
    r"""Pre-sanitize raw JSON string from LLMs to fix unescaped backslashes and invalid escapes.

    1. Preserves LaTeX math expressions in $...$ and $$...$$ by escaping unescaped commands.
    2. Replaces any single backslash not followed by a valid JSON escape sequence with a double backslash.
    """
    # Step 1: In math blocks ($...$ or $$...$$), double any single backslash before letters/commands
    def fix_math_escapes(match):
        math_content = match.group(0)
        return re.sub(r'(?<!\\)\\(?!\\)([a-zA-Z]+)', r'\\\\\1', math_content)

    raw_json = re.sub(r'\$\$[\s\S]*?\$\$', fix_math_escapes, raw_json)
    raw_json = re.sub(r'(?<![\w\\])\$([^\$\n]+?)\$(?![\w])', fix_math_escapes, raw_json)

    # Step 2: Fix any remaining single backslashes not followed by a valid JSON escape sequence
    pattern = r'(?<!\\)\\(?!\\)(?![/\"bfnrt]|u[0-9a-fA-F]{4})'
    return re.sub(pattern, r'\\\\', raw_json)


class RobustBaseModel(BaseModel):
    """Base Pydantic model that automatically repairs common LLM JSON output errors."""

    @classmethod
    def model_validate_json(
        cls,
        json_data: Union[str, bytes, bytearray],
        *,
        strict: Union[bool, None] = None,
        context: Union[dict, None] = None,
    ):
        """Validate a JSON string or bytes, with automatic repair for invalid escapes and syntax quirks."""
        if isinstance(json_data, (bytes, bytearray)):
            json_str = json_data.decode("utf-8")
        else:
            json_str = str(json_data)

        # 1. Try standard Pydantic JSON validation first
        try:
            return super().model_validate_json(json_str, strict=strict, context=context)
        except Exception:
            pass

        # 2. Try pre-sanitizing invalid backslashes (preserves LaTeX \sigma, code \ line continuations, etc.)
        try:
            sanitized = sanitize_json_string(json_str)
            return super().model_validate_json(sanitized, strict=strict, context=context)
        except Exception:
            pass

        # 3. Try with json_repair
        try:
            repaired = json_repair.repair_json(json_str)
            return super().model_validate_json(repaired, strict=strict, context=context)
        except Exception:
            pass

        # 4. Fallback: Parse object via json_repair and validate
        loaded = json_repair.loads(json_str)
        return cls.model_validate(loaded, strict=strict, context=context)

    @classmethod
    def model_validate(
        cls,
        obj: Any,
        *,
        strict: Union[bool, None] = None,
        from_attributes: Union[bool, None] = None,
        context: Union[dict, None] = None,
    ):
        """Validate Python objects, with string/JSON repair fallback if a raw string is provided."""
        if isinstance(obj, str):
            try:
                parsed = json.loads(obj)
                return super().model_validate(parsed, strict=strict, from_attributes=from_attributes, context=context)
            except Exception:
                try:
                    sanitized = sanitize_json_string(obj)
                    parsed = json.loads(sanitized)
                    return super().model_validate(parsed, strict=strict, from_attributes=from_attributes, context=context)
                except Exception:
                    repaired = json_repair.loads(obj)
                    return super().model_validate(repaired, strict=strict, from_attributes=from_attributes, context=context)

        return super().model_validate(obj, strict=strict, from_attributes=from_attributes, context=context)
