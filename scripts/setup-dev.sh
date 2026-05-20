#!/usr/bin/env bash
# 开发环境一键安装 / 刷新 CLI 入口 (odp-init, odp-reset)
# 用法 (项目根目录):
#   bash scripts/setup-dev.sh
#   bash scripts/setup-dev.sh --reinstall-only

set -euo pipefail
cd "$(dirname "$0")/.."

if [[ "${1:-}" == "--reinstall-only" ]]; then
  echo ">> 仅刷新 platform 包与 CLI 入口 (不装依赖)..."
  pip install -e ./apps/platform --force-reinstall --no-deps
else
  echo ">> 安装 platform 包 + 开发依赖..."
  pip install -r requirements-dev.txt
fi

echo ""
echo ">> 验证 CLI:"
command -v odp-init >/dev/null && echo "  odp-init  -> $(command -v odp-init)" || echo "  odp-init  -> 未找到"
command -v odp-reset >/dev/null && echo "  odp-reset -> $(command -v odp-reset)" || echo "  odp-reset -> 未找到"
echo ""
echo "完成。常用命令:"
echo "  odp-init"
echo "  odp-reset              # dry-run 预览"
echo "  odp-reset --yes        # 执行删除 (需输入 RESET)"
