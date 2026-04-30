from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass, field
from typing import Any


RUNTIME_CONFIG_SCHEMA_ID = "trader1.runtime_config.v1"
ALLOWED_CONFIG_KEYS = frozenset(
    {
        "schema_id",
        "project_id",
        "exchange",
        "market_type",
        "mode",
        "session_id",
        "registry_hash",
        "config_hash",
        "market_type_source",
        "market_type_defaulted",
        "live_entry_enabled",
        "allow_live_credentials",
        "live_order_ready",
        "live_order_allowed",
        "can_live_trade",
    }
)
REQUIRED_CONFIG_KEYS = frozenset(
    {
        "schema_id",
        "project_id",
        "exchange",
        "market_type",
        "mode",
        "session_id",
        "registry_hash",
        "config_hash",
        "market_type_source",
        "market_type_defaulted",
        "live_entry_enabled",
        "allow_live_credentials",
        "live_order_ready",
        "live_order_allowed",
        "can_live_trade",
    }
)
BINANCE_MARKET_TYPE_SOURCES = frozenset(
    {
        "SAFE_CONFIG_SCHEMA",
        "LAUNCHER_INTERNAL_UI",
        "EXPLICIT_COMMAND_OPTION",
    }
)


@dataclass(frozen=True)
class ConfigValidationResult:
    status: str
    message: str
    blockers: list[str] = field(default_factory=list)
    config_hash: str | None = None
    normalized_config: dict[str, Any] | None = None
    live_order_ready: bool = False
    live_order_allowed: bool = False
    can_live_trade: bool = False

    @property
    def primary_blocker_code(self) -> str | None:
        return self.blockers[0] if self.blockers else None


def config_hash(config: dict[str, Any]) -> str:
    payload = dict(config)
    payload.pop("config_hash", None)
    encoded = json.dumps(payload, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest().upper()


def attach_config_hash(config: dict[str, Any]) -> dict[str, Any]:
    normalized = dict(config)
    normalized["config_hash"] = config_hash(normalized)
    return normalized


def build_runtime_config(
    *,
    exchange: str,
    market_type: str,
    mode: str,
    session_id: str,
    registry_hash: str,
    market_type_source: str = "NOT_APPLICABLE",
) -> dict[str, Any]:
    config = {
        "schema_id": RUNTIME_CONFIG_SCHEMA_ID,
        "project_id": "TRADER_1",
        "exchange": exchange,
        "market_type": market_type,
        "mode": mode,
        "session_id": session_id,
        "registry_hash": registry_hash,
        "config_hash": "",
        "market_type_source": market_type_source,
        "market_type_defaulted": False,
        "live_entry_enabled": False,
        "allow_live_credentials": False,
        "live_order_ready": False,
        "live_order_allowed": False,
        "can_live_trade": False,
    }
    return attach_config_hash(config)


def _enum_values(registry: dict[str, Any], enum_name: str) -> set[str]:
    return set(registry.get("enums", {}).get(enum_name, {}).get("values", []))


def _blocked(message: str, blocker: str, config: dict[str, Any] | None = None) -> ConfigValidationResult:
    return ConfigValidationResult(
        status="BLOCKED",
        message=message,
        blockers=[blocker],
        config_hash=config_hash(config) if config is not None else None,
    )


def validate_runtime_config(
    config: dict[str, Any],
    registry: dict[str, Any],
    *,
    expected_registry_hash: str | None = None,
) -> ConfigValidationResult:
    if not isinstance(config, dict):
        return _blocked("runtime config must be an object", "SCHEMA_IDENTITY_MISMATCH")

    unknown = sorted(set(config) - ALLOWED_CONFIG_KEYS)
    if unknown:
        return _blocked(f"runtime config has unknown keys: {unknown}", "SCHEMA_IDENTITY_MISMATCH", config)

    missing = sorted(REQUIRED_CONFIG_KEYS - set(config))
    if missing:
        return _blocked(f"runtime config missing hard truth fields: {missing}", "HARD_TRUTH_MISSING", config)

    if config.get("schema_id") != RUNTIME_CONFIG_SCHEMA_ID or config.get("project_id") != "TRADER_1":
        return _blocked("runtime config identity mismatch", "SCHEMA_IDENTITY_MISMATCH", config)

    expected_hash = config_hash(config)
    if config.get("config_hash") != expected_hash:
        return _blocked("runtime config hash mismatch", "SCHEMA_IDENTITY_MISMATCH", config)

    registry_hash = config.get("registry_hash")
    if not isinstance(registry_hash, str) or not registry_hash:
        return _blocked("runtime config registry_hash missing", "HARD_TRUTH_MISSING", config)
    if expected_registry_hash is not None and registry_hash != expected_registry_hash:
        return _blocked("runtime config registry_hash does not match active registry", "SOURCE_IDENTITY_MISMATCH", config)

    exchange = config.get("exchange")
    market_type = config.get("market_type")
    mode = config.get("mode")
    if exchange not in _enum_values(registry, "exchange"):
        return _blocked("runtime config exchange not in registry", "REGISTRY_DRIFT", config)
    if market_type not in _enum_values(registry, "market_type"):
        return _blocked("runtime config market_type not in registry", "REGISTRY_DRIFT", config)
    if mode not in _enum_values(registry, "mode"):
        return _blocked("runtime config mode not in registry", "REGISTRY_DRIFT", config)

    if not isinstance(config.get("session_id"), str) or not config["session_id"].strip():
        return _blocked("runtime config session_id missing", "HARD_TRUTH_MISSING", config)

    if exchange == "UPBIT" and market_type != "KRW_SPOT":
        return _blocked("UPBIT runtime config must use KRW_SPOT market_type", "SNAPSHOT_SCOPE_MISMATCH", config)
    if exchange == "BINANCE" and market_type not in {"SPOT", "FUTURES_USDT_M"}:
        return _blocked("BINANCE runtime config must use SPOT or FUTURES_USDT_M", "SNAPSHOT_SCOPE_MISMATCH", config)

    source = config.get("market_type_source")
    if exchange == "UPBIT" and source != "NOT_APPLICABLE":
        return _blocked("UPBIT runtime config must not carry Binance market_type selector", "SNAPSHOT_SCOPE_MISMATCH", config)
    if exchange == "BINANCE" and source not in BINANCE_MARKET_TYPE_SOURCES:
        return _blocked("BINANCE runtime config requires explicit market_type selector", "SNAPSHOT_SCOPE_MISMATCH", config)
    if config.get("market_type_defaulted") is not False:
        return _blocked("runtime config market_type must not be implicit default", "SNAPSHOT_SCOPE_MISMATCH", config)

    live_flags = ("live_entry_enabled", "allow_live_credentials", "live_order_ready", "live_order_allowed", "can_live_trade")
    if any(config.get(flag) is not False for flag in live_flags):
        return _blocked("runtime config attempted to enable live capability without live-enabling evidence", "LIVE_FINAL_GUARD_FAILED", config)

    return ConfigValidationResult(
        status="PASS",
        message="runtime config is schema-scoped and fail-closed",
        blockers=[],
        config_hash=expected_hash,
        normalized_config=dict(config),
        live_order_ready=False,
        live_order_allowed=False,
        can_live_trade=False,
    )
