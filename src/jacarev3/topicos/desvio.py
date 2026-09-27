"""
jacarev3.topicos.desvio
-------------------------
Andar reto até achar obstáculo (sensor ultrassônico) e desviar.
"""

from __future__ import annotations

import time
from typing import TYPE_CHECKING, Optional

from .. import protocolo as p

if TYPE_CHECKING:
    from ..robo import RoboEV3


def desviar_obstaculo(
    robo: "RoboEV3",
    porta_sensor: object = 4,
    porta_motor_esquerdo: object = 'B',
    porta_motor_direito: object = 'C',
    velocidade: int = 30,
    distancia_minima_cm: float = 15,
    tempo_giro_s: float = 0.6,
    duracao_s: Optional[float] = None,
    verboso: bool = False,
) -> None:
    """
    Anda reto; quando o ultrassônico detecta algo mais perto que
    distancia_minima_cm, para, gira pra um lado por tempo_giro_s, e segue
    andando reto de novo.

    duracao_s: se informado, para sozinho depois desse tempo. Se None,
               roda até Ctrl+C.
    verboso: se True, imprime a distância lida a cada iteração.
    """
    print(f"Desviando de obstáculos (< {distancia_minima_cm}cm)... Ctrl+C pra parar.")
    inicio = time.time()
    try:
        while duracao_s is None or (time.time() - inicio) < duracao_s:
            distancia = robo.ler_sensor(porta_sensor, p.MODO_ULTRASSONICO_CM)

            if verboso:
                print(f"  distância={distancia}")

            if distancia is not None and distancia < distancia_minima_cm:
                print(f"  Obstáculo a {distancia:.1f}cm — desviando...")
                robo.parar_motor(porta_motor_esquerdo)
                robo.parar_motor(porta_motor_direito)
                time.sleep(0.1)

                # gira no lugar (motores em sentidos opostos)
                robo.mover_continuo(porta_motor_esquerdo, -velocidade)
                robo.mover_continuo(porta_motor_direito, velocidade)
                time.sleep(tempo_giro_s)
            else:
                robo.mover_continuo(porta_motor_esquerdo, velocidade)
                robo.mover_continuo(porta_motor_direito, velocidade)

            time.sleep(0.05)
    except KeyboardInterrupt:
        print("\nParado pelo usuário.")
    finally:
        robo.parar_motor(porta_motor_esquerdo)
        robo.parar_motor(porta_motor_direito)
