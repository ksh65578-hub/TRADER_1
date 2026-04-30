from __future__ import annotations

import json
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any


@dataclass(frozen=True)
class SchemaInstanceValidationResult:
    status: str
    message: str
    errors: list[str]


TYPE_MAP = {
    "object": dict,
    "array": list,
    "string": str,
    "boolean": bool,
    "null": type(None),
}


def load_schema_bundle(schema_dir: Path) -> dict[str, dict[str, Any]]:
    bundle: dict[str, dict[str, Any]] = {}
    for path in sorted(schema_dir.glob("*.schema.json")):
        schema = json.loads(path.read_text(encoding="utf-8"))
        bundle[path.name] = schema
        schema_id = schema.get("$id")
        if isinstance(schema_id, str):
            bundle[schema_id] = schema
    return bundle


def schema_for_instance(instance: Any, schema_bundle: dict[str, dict[str, Any]]) -> dict[str, Any] | None:
    if not isinstance(instance, dict):
        return None
    schema_id = instance.get("schema_id")
    if isinstance(schema_id, str) and schema_id in schema_bundle:
        return schema_bundle[schema_id]
    if isinstance(schema_id, str):
        for schema in schema_bundle.values():
            if schema.get("properties", {}).get("schema_id", {}).get("const") == schema_id:
                return schema
    return None


def validate_instance_against_schema(instance: Any, schema: dict[str, Any], schema_bundle: dict[str, dict[str, Any]]) -> SchemaInstanceValidationResult:
    errors: list[str] = []
    _validate(instance, schema, schema, schema_bundle, "$", errors)
    return SchemaInstanceValidationResult(
        "PASS" if not errors else "FAIL",
        "schema instance validation passed" if not errors else f"schema instance validation failed: {errors[0]}",
        errors,
    )


def _resolve_ref(ref: str, root_schema: dict[str, Any], schema_bundle: dict[str, dict[str, Any]]) -> tuple[dict[str, Any], dict[str, Any]] | None:
    if ref.startswith("#/"):
        target: Any = root_schema
        for part in ref[2:].split("/"):
            if not isinstance(target, dict) or part not in target:
                return None
            target = target[part]
        return (target, root_schema) if isinstance(target, dict) else None

    filename, _, pointer = ref.partition("#")
    external = schema_bundle.get(filename)
    if external is None:
        return None
    if not pointer:
        return external
    target = external
    for part in pointer.lstrip("/").split("/"):
        if not isinstance(target, dict) or part not in target:
            return None
        target = target[part]
    return (target, external) if isinstance(target, dict) else None


def _validate(instance: Any, schema: dict[str, Any], root_schema: dict[str, Any], schema_bundle: dict[str, dict[str, Any]], path: str, errors: list[str]) -> None:
    if errors:
        return

    ref = schema.get("$ref")
    if isinstance(ref, str):
        resolved_pair = _resolve_ref(ref, root_schema, schema_bundle)
        if resolved_pair is None:
            errors.append(f"{path}: unresolved $ref {ref}")
            return
        resolved, resolved_root = resolved_pair
        _validate(instance, resolved, resolved_root, schema_bundle, path, errors)
        return

    if "const" in schema and instance != schema["const"]:
        errors.append(f"{path}: expected const {schema['const']!r}, got {instance!r}")
        return
    if "enum" in schema and instance not in schema["enum"]:
        errors.append(f"{path}: value {instance!r} not in enum")
        return

    schema_type = schema.get("type")
    if schema_type is not None and not _matches_type(instance, schema_type):
        errors.append(f"{path}: expected type {schema_type}, got {type(instance).__name__}")
        return

    if isinstance(instance, str):
        min_length = schema.get("minLength")
        max_length = schema.get("maxLength")
        pattern = schema.get("pattern")
        if isinstance(min_length, int) and len(instance) < min_length:
            errors.append(f"{path}: string shorter than minLength {min_length}")
            return
        if isinstance(max_length, int) and len(instance) > max_length:
            errors.append(f"{path}: string longer than maxLength {max_length}")
            return
        if isinstance(pattern, str) and re.fullmatch(pattern, instance) is None:
            errors.append(f"{path}: string does not match pattern")
            return

    if isinstance(instance, (int, float)) and not isinstance(instance, bool):
        minimum = schema.get("minimum")
        if isinstance(minimum, (int, float)) and instance < minimum:
            errors.append(f"{path}: number below minimum {minimum}")
            return

    if isinstance(instance, dict):
        required = schema.get("required", [])
        if isinstance(required, list):
            for key in required:
                if key not in instance:
                    errors.append(f"{path}: missing required property {key}")
                    return
        properties = schema.get("properties", {})
        if schema.get("additionalProperties") is False and isinstance(properties, dict):
            extra = sorted(set(instance) - set(properties))
            if extra:
                errors.append(f"{path}: additional properties not allowed: {extra}")
                return
        if isinstance(properties, dict):
            for key, subschema in properties.items():
                if key in instance and isinstance(subschema, dict):
                    _validate(instance[key], subschema, root_schema, schema_bundle, f"{path}.{key}", errors)
                    if errors:
                        return

    if isinstance(instance, list):
        min_items = schema.get("minItems")
        max_items = schema.get("maxItems")
        if isinstance(min_items, int) and len(instance) < min_items:
            errors.append(f"{path}: array shorter than minItems {min_items}")
            return
        if isinstance(max_items, int) and len(instance) > max_items:
            errors.append(f"{path}: array longer than maxItems {max_items}")
            return
        item_schema = schema.get("items")
        if isinstance(item_schema, dict):
            for index, item in enumerate(instance):
                _validate(item, item_schema, root_schema, schema_bundle, f"{path}[{index}]", errors)
                if errors:
                    return


def _matches_type(instance: Any, schema_type: str | list[str]) -> bool:
    allowed = schema_type if isinstance(schema_type, list) else [schema_type]
    for item in allowed:
        if item == "integer" and isinstance(instance, int) and not isinstance(instance, bool):
            return True
        if item == "number" and isinstance(instance, (int, float)) and not isinstance(instance, bool):
            return True
        expected = TYPE_MAP.get(item)
        if expected is not None and isinstance(instance, expected):
            return True
    return False
