# -*- coding: utf-8 -*-
import pytest

from odp_platform.data_validation.registry import (
    CheckContext,
    CheckEntry,
    CheckResult,
    CheckSeverity,
    _REGISTRY,
    check,
)
from odp_platform.data_validation.service import run_all_checks
from odp_platform.data_validation.snapshot import build_snapshot


def test_check_severity_rank_order():
    assert CheckSeverity.rank(CheckSeverity.PASS) < CheckSeverity.rank(CheckSeverity.INFO)
    assert CheckSeverity.rank(CheckSeverity.INFO) < CheckSeverity.rank(CheckSeverity.WARNING)
    assert CheckSeverity.rank(CheckSeverity.WARNING) < CheckSeverity.rank(CheckSeverity.ERROR)


def test_duplicate_check_registration_raises():
    name = "_dup_test_ephemeral"
    _REGISTRY.pop(name, None)

    @check(name)
    def _a(ctx):
        return CheckResult(name, CheckSeverity.PASS, "ok", {})

    with pytest.raises(ValueError, match="已注册"):

        @check(name)
        def _b(ctx):
            return CheckResult(name, CheckSeverity.PASS, "ok", {})

    _REGISTRY.pop(name, None)


def test_check_result_passed_property():
    assert CheckResult("x", CheckSeverity.PASS, "ok", {}).passed
    assert CheckResult("x", CheckSeverity.INFO, "note", {}).passed
    assert not CheckResult("x", CheckSeverity.WARNING, "w", {}).passed
    assert not CheckResult("x", CheckSeverity.ERROR, "e", {}).passed


def test_run_all_checks_isolates_exceptions(healthy_yaml):
    snap = build_snapshot(healthy_yaml)
    ctx = CheckContext(yaml_path=healthy_yaml, snapshot=snap)

    from odp_platform.data_validation.registry import _ensure_checks_imported

    _ensure_checks_imported()
    old = _REGISTRY["yaml_schema"]

    def boom(_ctx):
        raise KeyError("boom")

    _REGISTRY["yaml_schema"] = CheckEntry(name="yaml_schema", func=boom)
    try:
        results = run_all_checks(ctx)
    finally:
        _REGISTRY["yaml_schema"] = old

    assert len(results) >= 4
    err = next(r for r in results if r.name == "yaml_schema")
    assert err.severity == CheckSeverity.ERROR
    assert err.details.get("exception_type") == "KeyError"
    others = [r for r in results if r.name != "yaml_schema"]
    assert all(r.severity in CheckSeverity._ORDER for r in others)


def test_list_checks_auto_import():
    from odp_platform.data_validation.registry import list_checks

    names = list_checks()
    assert "yaml_schema" in names
    assert "pair_existence" in names
    assert "label_format" in names
    assert "split_uniqueness" in names
