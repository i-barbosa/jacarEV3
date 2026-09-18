"""
jacarev3.teclado
----------------
Leitura de teclas sem bloquear, no Windows e no Linux/macOS, usando só a
biblioteca padrão. Não sabe nada sobre robôs — serve pra qualquer tópico
que precise de entrada de teclado ao vivo.

    from jacarev3.teclado import Teclado

    with Teclado() as teclado:
        while True:
            tecla = teclado.tecla()   # None se ninguém apertou nada

Precisa ser usado como gerenciador de contexto: no Linux ele coloca o
terminal em modo cru e o __exit__ é quem devolve a configuração antiga.
"""

import sys

__all__ = ["Teclado"]


if sys.platform == "win32":
    import msvcrt

    class Teclado:
        """Lê teclas no Windows via msvcrt."""

        def __enter__(self):
            return self

        def __exit__(self, *exc):
            return False

        def tecla(self):
            """Devolve a tecla apertada em minúscula, ou None."""
            if msvcrt.kbhit():
                return msvcrt.getwch().lower()
            return None

else:
    import select
    import termios
    import tty

    class Teclado:
        """Lê teclas no Linux/macOS colocando o terminal em modo cru."""

        def __enter__(self):
            self._fd = sys.stdin.fileno()
            self._config_antiga = termios.tcgetattr(self._fd)
            tty.setcbreak(self._fd)
            return self

        def __exit__(self, *exc):
            termios.tcsetattr(self._fd, termios.TCSADRAIN, self._config_antiga)
            return False

        def tecla(self):
            """Devolve a tecla apertada em minúscula, ou None."""
            pronto, _, _ = select.select([sys.stdin], [], [], 0)
            if pronto:
                return sys.stdin.read(1).lower()
            return None
