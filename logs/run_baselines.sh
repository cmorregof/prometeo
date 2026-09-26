#!/bin/sh
cd "$(dirname "$0")/.."
echo "inicio $(date)"
.venv/bin/python -u tools/baseline_paper.py --target bisection
echo "baseline fin $(date)"
.venv/bin/python -u tools/sh_goal.py --timeout 60
echo "fin $(date)"
