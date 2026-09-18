"""
jacarev3
--------
Lib em português pra controlar o LEGO EV3 via Bluetooth.

    from jacarev3 import RoboEV3, protocolo as p
    from jacarev3.topicos import circuito

O `pyproject.toml` lê a versão daqui (setuptools dynamic), então esse é o
único lugar onde o número de versão aparece.
"""

from . import fontes, protocolo, teclado, topicos
from .robo import RoboEV3

__all__ = ["RoboEV3", "fontes", "protocolo", "teclado", "topicos"]
__version__ = "0.4.0"
