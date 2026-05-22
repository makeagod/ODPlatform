# -*- coding: utf-8 -*-
from __future__ import annotations

import logging

from odp_platform.common.paths import APP_DIR, LOGGING_DIR, META_DIR, META_LOGGING_DIR
from odp_platform.logging import ROOT_LOGGER_NAME, get_logger, setup_cli_logging


def test_logging_dirs_under_apps_platform():
    assert LOGGING_DIR == APP_DIR / "logs"
    assert META_DIR == APP_DIR / ".odp-meta"
    assert META_LOGGING_DIR == META_DIR / "logs"


def test_setup_cli_logging_writes_file(tmp_path, monkeypatch):
    monkeypatch.setattr("odp_platform.logging.cli.LOGGING_DIR", tmp_path / "logs")
    setup_cli_logging("pytest_cli", temp_log=True)
    log_root = tmp_path / "logs" / "pytest_cli"
    assert log_root.is_dir()
    assert any(p.suffix == ".log" for p in log_root.iterdir())


def test_get_logger_idempotent(tmp_path):
    base = tmp_path / "logs"
    a = get_logger(base_path=base, log_type="once", logger_name="odp_platform.test.idempotent")
    b = get_logger(base_path=base, log_type="once", logger_name="odp_platform.test.idempotent")
    assert a is b
    assert len(a.handlers) == 2


def test_child_logger_bubbles_to_root(tmp_path):
    get_logger(
        base_path=tmp_path / "logs",
        log_type="bubble",
        logger_name=ROOT_LOGGER_NAME,
    )
    child = logging.getLogger("odp_platform.tests.child")
    child.info("bubble test message")
