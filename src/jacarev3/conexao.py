"""
jacarev3.conexao
--------------
Transporte de baixo nível: manda/recebe os pacotes crus montados pelo
módulo `protocolo`, por Bluetooth clássico (RFCOMM) ou USB (HID).

`ConexaoBluetooth` usa só a biblioteca padrão do Python (`socket` com
AF_BLUETOOTH), sem dependência externa — funciona no Windows (10+) e no
Linux com BlueZ.
"""

from __future__ import annotations

import contextlib
import itertools
import socket
import struct
from types import TracebackType
from typing import Any, Optional

from .erros import ErroDeConexaoBluetooth, ErroDeConexaoUSB, TempoEsgotado


class ConexaoBluetooth:
    """Conexão RFCOMM clássica com o EV3 (a mesma usada pelo app oficial)."""

    CANAL_RFCOMM_PADRAO = 1

    def __init__(self, mac: str, canal: Optional[int] = None, timeout: float = 10) -> None:
        self.mac = mac
        self.canal = canal or self.CANAL_RFCOMM_PADRAO
        self._contador = itertools.count(1)
        self.socket = socket.socket(
            socket.AF_BLUETOOTH, socket.SOCK_STREAM, socket.BTPROTO_RFCOMM
        )
        self.socket.settimeout(timeout)
        try:
            self.socket.connect((self.mac, self.canal))
        except TimeoutError as e:
            self.socket.close()
            raise TempoEsgotado(
                f"EV3 não respondeu em {timeout}s tentando conectar em "
                f"{self.mac} (canal {self.canal}). Confere se o EV3 tá "
                f"ligado e com Bluetooth ativo."
            ) from e
        except OSError as e:
            self.socket.close()
            raise ErroDeConexaoBluetooth(
                f"Não deu pra conectar em {self.mac} (canal {self.canal}): "
                f"{e}. Confere se o EV3 tá pareado nas configurações de "
                f"Bluetooth do sistema."
            ) from e

    def proximo_contador(self) -> int:
        return next(self._contador) & 0xFFFF

    def enviar(self, pacote: bytes) -> None:
        try:
            self.socket.sendall(pacote)
        except TimeoutError as e:
            raise TempoEsgotado("Demorou demais pra mandar o comando pro EV3.") from e
        except OSError as e:
            raise ErroDeConexaoBluetooth(f"Conexão com o EV3 caiu ao enviar: {e}") from e

    def receber(self, tamanho_max: int = 1024) -> bytes:
        try:
            dados = self.socket.recv(tamanho_max)
        except TimeoutError as e:
            raise TempoEsgotado("EV3 não respondeu a tempo.") from e
        except OSError as e:
            raise ErroDeConexaoBluetooth(f"Conexão com o EV3 caiu ao receber: {e}") from e
        if not dados:
            raise ErroDeConexaoBluetooth("EV3 fechou a conexão (recv vazio).")
        return dados

    def fechar(self) -> None:
        with contextlib.suppress(OSError):
            self.socket.close()

    def __enter__(self) -> ConexaoBluetooth:
        return self

    def __exit__(
        self,
        exc_type: Optional[type[BaseException]],
        exc: Optional[BaseException],
        tb: Optional[TracebackType],
    ) -> None:
        self.fechar()


VID_LEGO = 0x0694
PID_EV3 = 0x0005
TAMANHO_RELATORIO_USB = 1024  # fixo — mesmo valor usado por outras implementações


class ConexaoUSB:
    """Conexão via USB HID com o EV3.

    O EV3 aparece como um dispositivo HID USB comum (VID 0x0694, PID
    0x0005) — não precisa de driver especial em nenhum sistema
    (Windows/Linux/macOS), porque HID já usa a pilha nativa do próprio
    sistema operacional pra teclado/mouse. Isso é diferente de falar
    USB via `pyusb`/libusb, que no Windows exigiria trocar o driver do
    dispositivo por WinUSB (com uma ferramenta tipo Zadig, precisando
    de admin) — exatamente o tipo de fricção ruim numa sala de aula que
    essa lib tenta evitar.

    Formato do relatório HID, confirmado contra duas implementações
    independentes já testadas em hardware físico (BrianPeek/legoev3 em
    C#, ChristophGaukel/ev3-python3 em Python — ambas fazem o
    equivalente ao aqui, cada uma no seu jeito):
      - 1024 bytes fixos, tanto escrevendo quanto lendo.
      - Byte 0 é o "report ID" — o EV3 só tem um relatório, então esse
        byte é sempre 0x00, tanto mandando quanto recebendo.
      - Byte 1 em diante é o frame do Direct Command inteiro, do jeito
        que `protocolo.Comando.montar()` já produz (byte 0-1 dele é o
        próprio campo de tamanho, 2-3 o contador, ...) — sem nenhuma
        transformação a mais. Só a entrega muda; o protocolo por cima
        do fio é idêntico ao do Bluetooth.

    AVISO: implementado a partir de documentação pública e das duas
    referências citadas acima — **ainda não foi testado contra um EV3
    físico por USB nessa lib**. Testa com calma e reporta qualquer
    comportamento estranho.

    Precisa de `pip install jacarev3[usb]` — `hidapi` é uma dependência
    opcional, importada só aqui dentro, quando essa classe é usada.
    """

    def __init__(
        self,
        serie: Optional[str] = None,
        timeout: float = 10,
        modulo_hid: Optional[Any] = None,
    ) -> None:
        """
        serie: número de série do EV3, se tiver mais de um plugado.
               Sem isso, conecta no primeiro que achar.
        modulo_hid: módulo `hid` já importado, no lugar de importar de
                    verdade — é o que permite testar essa conexão sem
                    hardware nem hidapi instalado.
        """
        self.serie = serie
        self.timeout_ms = int(timeout * 1000)
        self._contador = itertools.count(1)

        if modulo_hid is None:
            import hid  # pacote "hidapi" no PyPI; importa como "hid"

            modulo_hid = hid

        self._dispositivo: Any = modulo_hid.device()
        try:
            if self.serie:
                self._dispositivo.open(VID_LEGO, PID_EV3, self.serie)
            else:
                self._dispositivo.open(VID_LEGO, PID_EV3)
        except OSError as e:
            raise ErroDeConexaoUSB(
                f"Não achei um EV3 por USB (VID {VID_LEGO:#06x}, PID {PID_EV3:#06x}): "
                f"{e}. Confere se o EV3 tá ligado e o cabo USB conectado."
            ) from e

    def proximo_contador(self) -> int:
        return next(self._contador) & 0xFFFF

    def enviar(self, pacote: bytes) -> None:
        relatorio = bytes([0]) + pacote  # byte 0 = report ID, sempre 0x00
        if len(relatorio) > TAMANHO_RELATORIO_USB:
            raise ErroDeConexaoUSB(
                f"Comando grande demais pro relatório USB "
                f"({len(relatorio)} > {TAMANHO_RELATORIO_USB} bytes)."
            )
        relatorio += bytes(TAMANHO_RELATORIO_USB - len(relatorio))  # preenche até 1024
        try:
            self._dispositivo.write(relatorio)
        except OSError as e:
            raise ErroDeConexaoUSB(f"Conexão USB com o EV3 caiu ao enviar: {e}") from e

    def receber(self, tamanho_max: int = TAMANHO_RELATORIO_USB) -> bytes:
        try:
            relatorio = bytes(self._dispositivo.read(TAMANHO_RELATORIO_USB, self.timeout_ms))
        except OSError as e:
            raise ErroDeConexaoUSB(f"Conexão USB com o EV3 caiu ao receber: {e}") from e
        if not relatorio:
            raise TempoEsgotado("EV3 não respondeu a tempo (USB).")
        # byte 0 = report ID (ignora); byte 1-2 = tamanho do Direct Command
        # (mesmo campo que protocolo.parse_resposta já sabe ler); o resto
        # do frame começa em seguida.
        tamanho = struct.unpack_from('<H', relatorio, 1)[0]
        return relatorio[1:3 + tamanho]

    def fechar(self) -> None:
        with contextlib.suppress(OSError):
            self._dispositivo.close()

    def __enter__(self) -> ConexaoUSB:
        return self

    def __exit__(
        self,
        exc_type: Optional[type[BaseException]],
        exc: Optional[BaseException],
        tb: Optional[TracebackType],
    ) -> None:
        self.fechar()


# Espaço reservado pro transporte WiFi no futuro:
#   ConexaoWiFi -> socket TCP na porta 5555 + handshake de "unlock"
