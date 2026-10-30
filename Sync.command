#!/bin/bash

cd "$HOME/MyAI" || exit 1

bash scripts/sync.sh

echo ""
echo "按回车键关闭窗口..."
read
