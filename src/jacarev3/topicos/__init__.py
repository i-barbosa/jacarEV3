"""
jacarev3.topicos
-----------------
"Receitas" prontas pra tarefas clássicas de robótica educacional, feitas
em cima do RoboEV3 básico. Cada módulo aqui é um tópico de aula/oficina.

Uso:
    from jacarev3 import RoboEV3
    from jacarev3.topicos import circuito

    with RoboEV3('00:16:53:64:F8:B8') as robo:
        circuito.seguir_linha(robo, porta_sensor=1)
"""

from . import circuito, controle, desvio

__all__ = ["circuito", "controle", "desvio"]
