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

from __future__ import annotations

from enum import Enum, auto
from typing import (
    Any,
    Dict,
    Final,
    Literal,
    Optional,
    Protocol,
    Tuple,
    Union,
    runtime_checkable,
)

from .teclado import Teclado

__all__ = ["SAIR", "TECLAS_PADRAO", "Fonte", "FontePygame", "FonteTeclado", "FonteUDP", "Leitura"]


class _Sinal(Enum):
    """Existe só pra SAIR ter um tipo de verdade — Enum de 1 membro é o
    jeito que o mypy sabe estreitar corretamente num `is SAIR`, ao
    contrário de um `object()` cru ou uma classe sentinela comum."""

    SAIR = auto()

    def __repr__(self) -> str:
        return "SAIR"


SAIR: Final = _Sinal.SAIR   # sentinela devolvida por ler() pra encerrar o controle

# O que ler() pode devolver: nada de novo, um estado (velocidade, giro),
# ou o pedido pra encerrar.
Leitura = Union[Tuple[float, float], _Sinal, None]


@runtime_checkable
class Fonte(Protocol):
    """O que `controle_remoto()` precisa de uma fonte. `ajuda()` é
    opcional (checado com `hasattr`), por isso não faz parte do
    contrato formal aqui."""

    def __enter__(self) -> "Fonte":
        ...

    def __exit__(self, *exc: object) -> bool:
        ...

    def ler(self) -> Leitura:
        ...


# tecla -> (fator de velocidade, fator de direção)
TECLAS_PADRAO: Dict[str, Tuple[float, float]] = {
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

    def __init__(
        self,
        teclas: Optional[Dict[str, Tuple[float, float]]] = None,
        tecla_parar: str = ' ',
        tecla_sair: str = 'q',
    ) -> None:
        self.teclas = dict(teclas or TECLAS_PADRAO)
        self.tecla_parar = tecla_parar
        self.tecla_sair = tecla_sair
        self._teclado: Optional[Teclado] = None

    def __enter__(self) -> "FonteTeclado":
        self._teclado = Teclado().__enter__()
        return self

    def __exit__(self, *exc: object) -> Literal[False]:
        assert self._teclado is not None
        self._teclado.__exit__(*exc)
        self._teclado = None
        return False

    def ler(self) -> Leitura:
        assert self._teclado is not None
        tecla = self._teclado.tecla()
        if tecla is None:
            return None
        if tecla == self.tecla_sair:
            return SAIR
        if tecla == self.tecla_parar:
            return (0, 0)
        return self.teclas.get(tecla)

    def ajuda(self) -> str:
        return "W frente, S ré, A esquerda, D direita, espaço para, Q sai"


class FontePygame:
    """Comandos vindos de um controle (Xbox/joystick) via pygame.

    Estilo "carro": os gatilhos RT/LT aceleram e dão ré (um cancela o
    outro se os dois forem apertados), e o analógico esquerdo
    (horizontal) faz a curva. Aplica zona morta no giro e suaviza a
    resposta ao longo do tempo, pra não sair puxando um repuxão a cada
    leitura do eixo — os valores padrão são os que já foram calibrados
    testando num Xbox 360 real, no Windows.

    `pygame` **não é** dependência da lib (`pip install jacarev3[pygame]`
    pra ganhar) — só é importado aqui dentro, quando essa fonte é usada
    de verdade.
    """

    def __init__(
        self,
        indice: int = 0,
        eixo_giro: int = 0,
        eixo_lt: int = 4,
        eixo_rt: int = 5,
        botao_sair: int = 0,
        zona_morta_giro: float = 0.1,
        taxa_suavizacao: float = 0.25,
        pygame: Optional[Any] = None,
    ) -> None:
        """
        indice: qual joystick usar, se tiver mais de um plugado
        eixo_giro: eixo do analógico usado pra curva (padrão: esquerdo,
                   horizontal)
        eixo_lt / eixo_rt: eixos dos gatilhos de ré / frente
        botao_sair: botão que encerra o controle_remoto()
        zona_morta_giro: abaixo desse valor absoluto, o giro vira 0 —
                         evita curva fantasma por folga do analógico
        taxa_suavizacao: 0-1, quanto mais alto mais direta a resposta
                         (1 = sem suavização nenhuma)
        pygame: módulo já importado, no lugar de importar de verdade —
                é o que permite testar essa fonte sem controle físico
                nem pygame instalado
        """
        self.indice = indice
        self.eixo_giro = eixo_giro
        self.eixo_lt = eixo_lt
        self.eixo_rt = eixo_rt
        self.botao_sair = botao_sair
        self.zona_morta_giro = zona_morta_giro
        self.taxa_suavizacao = taxa_suavizacao
        self._pygame: Optional[Any] = pygame
        self._joystick: Optional[Any] = None
        self._vel_atual = 0.0
        self._giro_atual = 0.0

    def __enter__(self) -> "FontePygame":
        if self._pygame is None:
            import pygame

            self._pygame = pygame

        self._pygame.init()
        self._pygame.joystick.init()

        if self._pygame.joystick.get_count() == 0:
            raise RuntimeError(
                "Nenhum controle detectado. Conecta o controle antes de rodar."
            )

        self._joystick = self._pygame.joystick.Joystick(self.indice)
        self._joystick.init()
        self._vel_atual = 0.0
        self._giro_atual = 0.0
        return self

    def __exit__(self, *exc: object) -> Literal[False]:
        assert self._pygame is not None
        self._pygame.joystick.quit()
        self._pygame.quit()
        self._joystick = None
        return False

    def ler(self) -> Leitura:
        assert self._pygame is not None and self._joystick is not None
        self._pygame.event.pump()
        joystick = self._joystick

        if joystick.get_button(self.botao_sair):
            return SAIR

        rt = self._normalizar_gatilho(joystick.get_axis(self.eixo_rt))
        lt = self._normalizar_gatilho(joystick.get_axis(self.eixo_lt))
        giro_bruto = self._zona_morta(joystick.get_axis(self.eixo_giro))

        self._vel_atual += (rt - lt - self._vel_atual) * self.taxa_suavizacao
        self._giro_atual += (giro_bruto - self._giro_atual) * self.taxa_suavizacao

        return (self._vel_atual, self._giro_atual)

    @staticmethod
    def _normalizar_gatilho(valor: float) -> float:
        """Gatilho pode vir de -1 (solto) a 1 (fundo) OU de 0 a 1, depende
        do driver. Normaliza pra sempre ficar 0 (solto) a 1 (fundo)."""
        if valor < -0.05:
            return (valor + 1) / 2
        return max(0.0, valor)

    def _zona_morta(self, valor: float) -> float:
        return 0.0 if abs(valor) < self.zona_morta_giro else valor

    def ajuda(self) -> str:
        return "RT acelera, LT dá ré, analógico esquerdo faz curva, botão pra sair"


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

    def __init__(self, porta: int = 9000, endereco: str = '0.0.0.0') -> None:
        self.porta = porta
        self.endereco = endereco
        self.socket: Optional[Any] = None
        self.ultimo_remetente: Optional[Tuple[str, int]] = None

    def __enter__(self) -> "FonteUDP":
        import socket

        self.socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.socket.bind((self.endereco, self.porta))
        self.socket.setblocking(False)
        return self

    def __exit__(self, *exc: object) -> Literal[False]:
        assert self.socket is not None
        self.socket.close()
        self.socket = None
        return False

    def ler(self) -> Leitura:
        """Pega o datagrama mais recente e descarta os atrasados."""
        assert self.socket is not None
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
    def _interpretar(dados: bytes) -> Union[Tuple[float, float], None]:
        try:
            partes = dados.decode('ascii').strip().split()
            velocidade, direcao = float(partes[0]), float(partes[1])
        except (UnicodeDecodeError, ValueError, IndexError):
            return None   # pacote estranho: ignora, o próximo vem logo

        def limite(v: float) -> float:
            return max(-1.0, min(1.0, v))

        return (limite(velocidade), limite(direcao))

    def ajuda(self) -> str:
        return f"Esperando o controle mandar pacotes UDP na porta {self.porta}"
