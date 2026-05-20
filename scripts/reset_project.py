#!/usr/bin/env python
# -*- coding:utf-8 -*-
"""工作区入口: python scripts/reset_project.py [--dry-run|--yes]"""

import sys
from pathlib import Path

_src = Path(__file__).resolve().parents[1] / "apps" / "platform" / "src"
if str(_src) not in sys.path:
    sys.path.insert(0, str(_src))

from odp_platform.cli.reset_project import main

if __name__ == "__main__":
    sys.exit(main())
