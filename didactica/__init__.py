"""didactica: los seis agentes tabulares de la serie (bisección, punto fijo, Taylor, Newton, secante e
interpolación), con un único `QAgent` compartido (`qagent.py`). Cada método es un subpaquete con su entorno,
su grafo de lemas, su entrenador, su interfaz y su informe:

    python -m didactica.biseccion --no-tui --seed 1      # o punto_fijo, taylor, newton, secante, interpolacion
    python -m didactica biseccion --no-tui --seed 1      # equivalente
"""

__version__ = "0.2.0"
