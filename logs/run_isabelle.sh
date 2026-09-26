#!/bin/sh
# Corridas del juez Isabelle, en serie (dos compilaciones simultáneas de la misma sesión chocan y
# la contención de CPU cambiaría qué encuentra Sledgehammer en 60 s).
cd "$(dirname "$0")/.."
echo "inicio $(date)"
.venv/bin/python -u -m unirl run --config configs/bisection_isabelle.toml --episodes 3 --model gpt-6-luna --effort high
echo "luna fin $(date)"
.venv/bin/python -u -m unirl run --config configs/bisection_isabelle.toml --episodes 3 --model gpt-5.4-mini --effort low
echo "fin $(date)"
