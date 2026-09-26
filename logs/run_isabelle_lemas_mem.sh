#!/bin/sh
# V_I con lemas auxiliares y MEMORIA entre episodios, gpt-6-luna (high), 3 episodios, B = 4. En serie.
cd "$(dirname "$0")/.."
echo "inicio $(date)"
.venv/bin/python -u -m unirl run --config configs/bisection_isabelle_lemas_mem.toml --episodes 3
echo "fin $(date)"
