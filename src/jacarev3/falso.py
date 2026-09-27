"""
jacarev3.falso
--------------
Um "EV3 de mentira": implementa o mesmo contrato que `ConexaoBluetooth`/
`ConexaoUSB` (`jacarev3.transporte.Transporte`), mas nunca toca em rede
nem hardware nenhum. Serve pra:

  - Dar aula inteira sem robô físico — todo mundo com computador já
    consegue rodar o código, ver o print de "o que aconteceria", e
    testar a lógica antes de chegar num EV3 de verdade
  - Escrever teste automatizado da sua própria lógica de robô

    from jacarev3 import RoboEV3
    from jacarev3.falso import ConexaoFalsa

    with RoboEV3(conexao=ConexaoFalsa()) as robo:
        robo.apitar()
        robo.led('VERDE')
        print(robo.ler_sensor(1, 0))   # 50.0 (valor sintético padrão)

Sensor devolve sempre o mesmo valor por padrão (configurável) — não
simula física nenhuma. Não é um simulador, é uma dublê: existe pra
código rodar sem travar esperando um robô que não tá plugado.
"""

from __future__ import annotations

import itertools
import struct
from typing import Callable, Dict, List, Optional, Tuple, Union

from . import protocolo as p

# Nomes amigáveis só pros opcodes que essa lib usa — não é um decodificador
# de bytecode completo, só o suficiente pra imprimir algo legível na aula.
_NOMES_OPCODE = {
    p.opSOUND: "som (apitar)",
    p.opUI_WRITE: "LED",
    p.opOUTPUT_RESET: "motor: reset",
    p.opOUTPUT_STOP: "motor: parar",
    p.opOUTPUT_SPEED: "motor: definir velocidade",
    p.opOUTPUT_START: "motor: ligar",
    p.opOUTPUT_TEST: "motor: perguntar se tá ocupado",
    p.opOUTPUT_STEP_SPEED: "motor: girar por graus",
    p.opOUTPUT_TIME_SPEED: "motor: girar por tempo",
    p.opOUTPUT_STEP_SYNC: "base: mover por graus",
    p.opOUTPUT_TIME_SYNC: "base: mover por tempo",
    p.opOUTPUT_CLR_COUNT: "motor: zerar encoder",
    p.opOUTPUT_GET_COUNT: "motor: ler encoder",
    p.opINPUT_DEVICE: "sensor: ler",
}

# posição, dentro do pacote inteiro, onde o bytecode do comando começa
# (4 bytes de tamanho+contador, 1 de tipo, 2 de alocação de variáveis)
_INICIO_BYTECODE = 7

ValorSensor = Union[float, Callable[[int, int], float]]


class ConexaoFalsa:
    """Dublê de conexão — nunca abre socket nem dispositivo nenhum."""

    def __init__(
        self,
        valores_sensor: Optional[Dict[Tuple[int, int], ValorSensor]] = None,
        valor_padrao: float = 50.0,
        verboso: bool = True,
    ) -> None:
        """
        valores_sensor: dict {(porta_indice_0_a_3, modo): valor_ou_funcao}.
            `valor_ou_funcao` pode ser um número fixo, ou uma função
            `(porta, modo) -> float` chamada a cada leitura (pra
            simular sensor mudando ao longo do tempo).
            Porta aqui é o índice interno 0-3 (porta física - 1) — o
            mesmo valor que apareceria no bytecode enviado.
        valor_padrao: valor devolvido pra qualquer leitura de sensor
            que não tenha entrada em `valores_sensor`.
        verboso: se True, imprime cada comando "executado" — é o que
            faz a aula sem robô ainda parecer que algo tá acontecendo.
        """
        self.valores_sensor = valores_sensor or {}
        self.valor_padrao = valor_padrao
        self.verboso = verboso
        self._contador = itertools.count(1)
        self.enviados: List[bytes] = []  # todo pacote que "saiu", na ordem — útil em teste
        self._ultimo_pacote: bytes = b''

    def proximo_contador(self) -> int:
        return next(self._contador) & 0xFFFF

    def enviar(self, pacote: bytes) -> None:
        self.enviados.append(pacote)
        if self.verboso:
            print(f"[robô de mentira] {self._descrever(pacote)}")
        self._ultimo_pacote = pacote

    def receber(self, tamanho_max: int = 1024) -> bytes:
        """Fabrica uma resposta plausível a partir do último pacote
        enviado — nunca é chamada sem um enviar() antes (mesma regra
        de ConexaoBluetooth/ConexaoUSB: RoboEV3 só chama receber()
        logo depois de um enviar() com com_resposta=True)."""
        contador, bytes_globais = self._info_ultimo_pacote()
        payload = self._fabricar_payload(bytes_globais)
        corpo = bytes([p.DIRECT_REPLY_OK]) + payload
        return struct.pack('<HH', 2 + len(corpo), contador) + corpo

    def fechar(self) -> None:
        pass

    def __enter__(self) -> "ConexaoFalsa":
        return self

    def __exit__(self, *exc: object) -> None:
        self.fechar()

    # ---------- por dentro ----------

    def _info_ultimo_pacote(self) -> Tuple[int, int]:
        pacote = self._ultimo_pacote
        _, contador = struct.unpack_from('<HH', pacote, 0)
        bytes_globais = pacote[5] | ((pacote[6] & 0x03) << 8)
        return contador, bytes_globais

    def _fabricar_payload(self, bytes_globais: int) -> bytes:
        leitura = self._decodificar_leitura_sensor(self._ultimo_pacote)
        if leitura is not None and bytes_globais >= 4:
            porta, modo = leitura
            valor = self.valores_sensor.get((porta, modo), self.valor_padrao)
            if callable(valor):
                valor = valor(porta, modo)
            return struct.pack('<f', float(valor))
        return bytes(bytes_globais)  # zero serve pra int32=0 (encoder) e int8=0 (não ocupado)

    @staticmethod
    def _decodificar_leitura_sensor(pacote: bytes) -> Optional[Tuple[int, int]]:
        """Reconhece só o bytecode que _ler_sensor() monta — não é um
        decodificador de Direct Command genérico."""
        bytecode = pacote[_INICIO_BYTECODE:]
        if len(bytecode) < 6 or bytecode[0] != p.opINPUT_DEVICE:
            return None
        porta = bytecode[3] & 0x3F
        modo = bytecode[5] & 0x3F
        return porta, modo

    @staticmethod
    def _descrever(pacote: bytes) -> str:
        bytecode = pacote[_INICIO_BYTECODE:]
        if not bytecode:
            return "comando vazio"
        nome = _NOMES_OPCODE.get(bytecode[0])
        return nome if nome else f"comando desconhecido (opcode {bytecode[0]:#04x})"
