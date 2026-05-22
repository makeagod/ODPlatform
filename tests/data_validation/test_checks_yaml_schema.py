# -*- coding: utf-8 -*-
from odp_platform.data_validation.checks.yaml_schema import validate_yaml_schema
from odp_platform.data_validation.registry import CheckContext, CheckSeverity
from odp_platform.data_validation.snapshot import build_snapshot


def test_yaml_schema_pass(healthy_yaml):
    snap = build_snapshot(healthy_yaml)
    ctx = CheckContext(yaml_path=healthy_yaml, snapshot=snap)
    result = validate_yaml_schema(ctx)
    assert result.severity == CheckSeverity.PASS


def test_yaml_schema_nc_names_mismatch(bad_nc_names_yaml):
    snap = build_snapshot(bad_nc_names_yaml)
    ctx = CheckContext(yaml_path=bad_nc_names_yaml, snapshot=snap)
    result = validate_yaml_schema(ctx)
    assert result.severity == CheckSeverity.ERROR
    problems = result.details["problems"]
    assert any("nc (3)" in p and "names 长度 (2)" in p for p in problems)


def test_yaml_schema_missing_file(tmp_path):
    missing = tmp_path / "nope.yaml"
    snap = build_snapshot(missing)
    ctx = CheckContext(yaml_path=missing, snapshot=snap)
    result = validate_yaml_schema(ctx)
    assert result.severity == CheckSeverity.ERROR
    assert "不存在" in result.details["problems"][0]
