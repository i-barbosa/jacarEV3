"""
jacarev3.topicos.controle
-------------------------
Controle remoto: dirigir a base motriz de onde quiser.

O loop daqui não sabe de onde vem o comando. Ele pergunta pra uma
*fonte* (ver jacarev3.fontes) e manda pro robô. Teclado do PC, controle
de ESP32 pela rede, gamepad — tudo entra pela mesma porta.

    from jacarev3 import RoboEV3
    from jacarev3.fontes import FonteUDP
    from jacarev3.topicos import controle

    with RoboEV3('00:16:53:64:F8:B8') as robo:
        controle.controle_remoto(robo)                      # teclado
        controle.controle_remoto(robo, fonte=FonteUDP())    # ESP32

Como o robô para sozinho:
    Cada comando enviado é um opOUTPUT_TIME_SYNC com prazo curto (a
    "janela"). O EV3 desliga os motores quando esse prazo acaba, então o
    loop precisa renovar antes. Se o script travar, o Bluetooth cair, o
    controle ficar sem bateria ou sair do alcance, o robô para sozinho.
    Nenhum controle remoto deve depender de uma mensagem de "parar" que
    pode nunca chegar.
"""

import time

from ..fontes import SAIR, FonteTeclado

__all__ = ["controle_remoto"]


def controle_remoto(
    robo,
    fonte=None,
    velocidade=35,
    giro=100,
    janela_ms=400,
    intervalo=0.1,
    expira=0.25,
    verboso=False,
):
    """
    Dirige a base motriz até a fonte pedir pra sair (ou Ctrl+C).

    fonte: de onde vêm os comandos. Padrão: teclado do computador.
    velocidade: velocidade base, 1 a 100
    giro: quanto vira no comando de curva (0 a 200; 100 trava uma roda,
          200 gira no próprio eixo)
    janela_ms: prazo de cada comando no EV3 — quanto tempo o robô anda se
               parar de receber ordens
    intervalo: de quanto em quanto tempo o comando é renovado (precisa ser
               bem menor que janela_ms)
    expira: quanto tempo sem notícia da fonte até parar por segurança
    verboso: imprime cada comando enviado, bom pra aula

    Bloqueia até sair. Sempre para o robô na saída, inclusive com erro.
    """
    if not 0 < velocidade <= 100:
        raise ValueError("velocidade deve ficar entre 1 e 100")
    if intervalo >= janela_ms / 1000:
        raise ValueError("intervalo precisa ser menor que janela_ms, senão o robô engasga")

    fonte = fonte if fonte is not None else FonteTeclado()
    estado = None
    desde = 0.0
    ultimo_envio = 0.0

    try:
        with fonte:
            if hasattr(fonte, 'ajuda'):
                print(fonte.ajuda())

            while True:
                leitura = fonte.ler()
                agora = time.time()

                if leitura is SAIR:
                    break
                if leitura is not None:
                    estado = leitura
                    desde = agora

                # sem notícia faz tempo: o dedo saiu da tecla, ou o
                # controle sumiu. Nos dois casos, para.
                if estado is not None and agora - desde > expira:
                    estado = None

                if agora - ultimo_envio < intervalo:
                    time.sleep(0.01)
                    continue

                if estado is None or tuple(estado) == (0, 0):
                    robo.parar_base()
                else:
                    fator_velocidade, fator_giro = estado
                    v = int(velocidade * fator_velocidade)
                    d = int(giro * fator_giro)
                    robo.mover_base(velocidade=v, direcao=d, duracao_ms=janela_ms)
                    if verboso:
                        print(f"  velocidade={v} direcao={d}")

                ultimo_envio = agora
                time.sleep(0.01)
    except KeyboardInterrupt:
        pass
    finally:
        robo.parar_base()
        print("Controle encerrado.")
