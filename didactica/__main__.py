"""`python -m didactica <metodo> [opciones]`: lanza el método indicado. Equivale a `python -m didactica.<metodo>`."""

import importlib
import sys

METODOS = ("biseccion", "punto_fijo", "taylor", "newton", "secante", "interpolacion")


def main(argv=None) -> int:
    argv = list(sys.argv[1:] if argv is None else argv)
    if not argv or argv[0] not in METODOS:
        print("uso: python -m didactica <" + "|".join(METODOS) + "> [opciones]", file=sys.stderr)
        return 2
    cli = importlib.import_module(f"didactica.{argv[0]}.cli")
    sys.argv = [f"didactica.{argv[0]}", *argv[1:]]
    return cli.main()


if __name__ == "__main__":
    raise SystemExit(main())
