#!/bin/sh
# Repetición de gpt-5.4-mini bajo V_I con el extractor corregido (colisión de delimitador).
cd "$(dirname "$0")/.."
echo "inicio $(date)"
.venv/bin/python -u -m unirl run --config configs/bisection_isabelle.toml --episodes 3 --model gpt-5.4-mini --effort low
echo "fin $(date)"
