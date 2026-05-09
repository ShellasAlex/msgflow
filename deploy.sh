#!/bin/bash
# deploy.sh — 一键部署 Worker + 提交推送
# 用法: ./deploy.sh "commit message"

set -e

MSG="${1:-update}"
ROOT="$(cd "$(dirname "$0")" && pwd)"

echo "=== 部署 Worker ==="
cd "$ROOT/worker"
wrangler deploy

echo ""
echo "=== 提交并推送 ==="
cd "$ROOT"
git add .
if git diff --cached --quiet; then
  echo "没有变更需要提交"
else
  git commit -m "$MSG"
  git pull --rebase
  git push
fi

echo ""
echo "✅ 完成"
