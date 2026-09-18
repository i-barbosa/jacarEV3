"""
jacarev3.fontes
---------------
De onde vêm os comandos do controle remoto.

Uma fonte é qualquer objeto com um método `ler()` que devolve:

    None            nada novo desde a última vez
    (vel, direcao)  estado atual, como fatores de -1 a 1
    SAIR            o usuário pediu pra encerrar

Os fatores são multiplicados pela velocidade e pelo giro configurados no
controle. (0, 0) quer dizer "parado".

Fonte também é gerenciador de contexto: o `with` é quem configura e
desmonta o recurso (terminal cru, socket).

Escrever uma fonte nova (gamepad, celular, sensor) é implementar essas
duas coisas — o loop de controle não muda.
"""

import time

from .teclado import Teclado

__all__ = ["SAIR", "FonteTeclado", "FonteUDP", "TECLAS_PADRAO"]


SAIR = object()   # sentinela devolvida por ler() pra encerrar o controle


# tecla -> (fator de velocidade, fator de direção)
TECLAS_PADRAO = {
    'w': (1, 0),
    's': (-1, 0),
    'a': (1, -1),
    'd': (1, 1),
}


class FonteTeclado:
    """Comandos vindos do teclado do próprio computador.

    O terminal não avisa quando a tecla é solta — ele só repete enquanto
    ela fica apertada. Por isso essa fonte devolve None quando ninguém
    digita nada, e quem decide que o dedo saiu é a expiração do loop.
    """

    def __init__(self, teclas=None, tecla_parar=' ', tecla_sair='q'):
        self.teclas = dict(teclas or TECLAS_PADRAO)
        self.tecla_parar = tecla_parar
        self.tecla_sair = tecla_sair
        self._teclado = None

    def __enter__(self):
        self._teclado = Teclado().__enter__()
        return self

    def __exit__(self, *exc):
        self._teclado.__exit__(*exc)
        self._teclado = None
        return False

    def ler(self):
        tecla = self._teclado.tecla()
        if tecla is None:
            return None
        if tecla == self.tecla_sair:
            return SAIR
        if tecla == self.tecla_parar:
            return (0, 0)
        return self.teclas.get(tecla)

    def ajuda(self):
        return "W frente, S ré, A esquerda, D direita, espaço para, Q sai"


class FonteUDP:
    """Comandos vindos de um controle físico pela rede (ex: ESP32).

    O controle manda, de tempos em tempos, um datagrama de texto:

        "<fator_velocidade> <fator_direcao>"

    Exemplos: "1 0" anda pra frente, "1 1" vira pra direita, "0 0" para.

    UDP não garante entrega e não avisa quando a conexão cai — e isso
    aqui é uma vantagem: se o controle sair do alcance ou ficar sem
    bateria, os pacotes simplesmente param de chegar, a expiração do loop
    dispara e o robô para. Pacote perdido no meio também não atrapalha,
    porque o próximo já traz o estado inteiro de novo.
    """

    def __init__(self, porta=9000, endereco='0.0.0.0'):
        self.porta = porta
        self.endereco = endereco
        self.socket = None
        self.ultimo_remetente = None

    def __enter__(self):
        import socket

        self.socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.socket.bind((self.endereco, self.porta))
        self.socket.setblocking(False)
        return self

    def __exit__(self, *exc):
        self.socket.close()
        self.socket = None
        return False

    def ler(self):
        """Pega o datagrama mais recente e descarta os atrasados."""
        ultimo = None
        while True:
            try:
                dados, remetente = self.socket.recvfrom(64)
            except (BlockingIOError, OSError):
                break
            ultimo = dados
            self.ultimo_remetente = remetente

        if ultimo is None:
            return None
        return self._interpretar(ultimo)

    @staticmethod
    def _interpretar(dados):
        try:
            partes = dados.decode('ascii').strip().split()
            velocidade, direcao = float(partes[0]), float(partes[1])
        except (UnicodeDecodeError, ValueError, IndexError):
            return None   # pacote estranho: ignora, o próximo vem logo

        limite = lambda v: max(-1.0, min(1.0, v))
        return (limite(velocidade), limite(direcao))

    def ajuda(self):
        return f"Esperando o controle mandar pacotes UDP na porta {self.porta}"
