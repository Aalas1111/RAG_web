#!/bin/bash
# 重启网站示例脚本（Linux/服务器）
# 在 .env 中设置 RESTART_SCRIPT=scripts/restart.sh 后，管理界面「重启网站」会执行本脚本
# 请根据实际部署方式修改下方命令（Supervisor / systemd / 宝塔 等）

set -e
cd "$(dirname "$0")/.."

# 若使用 Supervisor 管理后端（程序名以你实际配置为准）
if command -v supervisorctl &>/dev/null; then
  supervisorctl restart rag_web_api 2>/dev/null || true
fi

# 若需重载 Nginx（静态前端）
if command -v nginx &>/dev/null; then
  nginx -t 2>/dev/null && nginx -s reload 2>/dev/null || true
fi

echo "Restart triggered."
