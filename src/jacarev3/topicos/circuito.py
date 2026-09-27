"""
jacarev3.topicos.circuito
---------------------------
Tarefas clássicas de "circuito": seguir linha preta com sensor de cor em
modo refletância (bang-bang, mais simples de entender pra quem tá
aprendendo — sem PID).

Montagem esperada: sensor de cor apontando pro chão, robô com 2 motores
(esquerda/direita) nas portas indicadas.
"""

from __future__ import annotations

import time
from typing import TYPE_CHECKING, List, Optional

from .. import protocolo as p

if TYPE_CHECKING:
    from ..robo import RoboEV3


def seguir_linha(
    robo: "RoboEV3",
    porta_sensor: object = 1,
    porta_motor_esquerdo: object = 'B',
    porta_motor_direito: object = 'C',
    velocidade: int = 25,
    limiar: Optional[float] = None,
    duracao_s: Optional[float] = None,
    verboso: bool = False,
) -> None:
    """
    Segue uma linha preta no chão branco (ou vice-versa) usando controle
    bang-bang: se o sensor vê "claro", gira pra um lado; se vê "escuro",
    gira pro outro. Bom ponto de partida pra ensinar o conceito antes de
    evoluir pra PID.

    porta_sensor: porta (1-4) do sensor de cor, em modo refletância
    porta_motor_esquerdo / porta_motor_direito: portas (A-D) dos motores
    velocidade: velocidade base (0-100)
    limiar: valor de refletância que separa "linha" de "fundo" (0-100).
            Se None, calibra automaticamente no começo (ver calibrar()).
    duracao_s: se informado, para sozinho depois desse tempo. Se None,
               roda até Ctrl+C.
    verboso: se True, imprime leitura e decisão a cada iteração — bom
             pra entender o que o loop tá fazendo (mais lento por causa
             do print, desliga quando já entendeu a lógica).
    """
    if limiar is None:
        limiar = calibrar(robo, porta_sensor)

    print(f"Seguindo linha (limiar={limiar:.1f})... Ctrl+C pra parar.")
    inicio = time.time()
    try:
        while duracao_s is None or (time.time() - inicio) < duracao_s:
            leitura = robo.ler_sensor(porta_sensor, p.MODO_COR_REFLETIDA)

            if leitura > limiar:
                # tá no "claro" -> puxa pra um lado (ajusta a lógica pro
                # seu robô: pode precisar inverter esquerda/direita)
                lado = "CLARO -> girando pra direita"
                robo.mover_continuo(porta_motor_esquerdo, velocidade)
                robo.mover_continuo(porta_motor_direito, velocidade // 3)
            else:
                # tá no "escuro" (linha) -> puxa pro outro lado
                lado = "ESCURO -> girando pra esquerda"
                robo.mover_continuo(porta_motor_esquerdo, velocidade // 3)
                robo.mover_continuo(porta_motor_direito, velocidade)

            if verboso:
                print(f"  leitura={leitura:.1f}  limiar={limiar:.1f}  decisão: {lado}")

            time.sleep(0.05)
    except KeyboardInterrupt:
        print("\nParado pelo usuário.")
    finally:
        robo.parar_motor(porta_motor_esquerdo)
        robo.parar_motor(porta_motor_direito)


def calibrar(
    robo: "RoboEV3", porta_sensor: object, amostras: int = 20, intervalo: float = 0.1
) -> float:
    """
    Calibração simples: pede pra passar o sensor por cima do "claro" e do
    "escuro" e calcula o ponto médio como limiar. Chamada automaticamente
    por seguir_linha() se você não passar um limiar manual.
    """
    print("Calibrando: posiciona o sensor sobre o FUNDO (claro) e espera...")
    time.sleep(2)
    claro = _media_leituras(robo, porta_sensor, amostras, intervalo)
    print(f"  Fundo claro: {claro:.1f}")

    print("Agora posiciona o sensor sobre a LINHA (escuro) e espera...")
    time.sleep(2)
    escuro = _media_leituras(robo, porta_sensor, amostras, intervalo)
    print(f"  Linha escura: {escuro:.1f}")

    limiar = (claro + escuro) / 2
    print(f"Limiar calculado: {limiar:.1f}\n")
    return limiar


def _media_leituras(
    robo: "RoboEV3", porta_sensor: object, amostras: int, intervalo: float
) -> float:
    valores: List[float] = []
    for _ in range(amostras):
        valores.append(robo.ler_sensor(porta_sensor, p.MODO_COR_REFLETIDA))
        time.sleep(intervalo)
    return sum(valores) / len(valores)
