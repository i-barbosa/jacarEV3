"""
jacarev3.conexao
--------------
Transporte de baixo nível: abre um socket Bluetooth clássico (RFCOMM) com o
EV3 e manda/recebe os pacotes crus montados pelo módulo `protocolo`.

Usa só a biblioteca padrão do Python (`socket` com AF_BLUETOOTH), sem
dependência externa — funciona no Windows (10+) e no Linux com BlueZ.
"""

import socket
import itertools

from .erros import ErroDeConexaoBluetooth, TempoEsgotado


class ConexaoBluetooth:
    """Conexão RFCOMM clássica com o EV3 (a mesma usada pelo app oficial)."""

    CANAL_RFCOMM_PADRAO = 1

    def __init__(self, mac, canal=None, timeout=10):
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

    def proximo_contador(self):
        return next(self._contador) & 0xFFFF

    def enviar(self, pacote):
        try:
            self.socket.sendall(pacote)
        except TimeoutError as e:
            raise TempoEsgotado("Demorou demais pra mandar o comando pro EV3.") from e
        except OSError as e:
            raise ErroDeConexaoBluetooth(f"Conexão com o EV3 caiu ao enviar: {e}") from e

    def receber(self, tamanho_max=1024):
        try:
            dados = self.socket.recv(tamanho_max)
        except TimeoutError as e:
            raise TempoEsgotado("EV3 não respondeu a tempo.") from e
        except OSError as e:
            raise ErroDeConexaoBluetooth(f"Conexão com o EV3 caiu ao receber: {e}") from e
        if not dados:
            raise ErroDeConexaoBluetooth("EV3 fechou a conexão (recv vazio).")
        return dados

    def fechar(self):
        try:
            self.socket.close()
        except OSError:
            pass

    def __enter__(self):
        return self

    def __exit__(self, *exc):
        self.fechar()


# Espaço reservado pra outros transportes (WiFi/USB) no futuro:
#   ConexaoWiFi   -> socket TCP na porta 5555 + handshake de "unlock"
#   ConexaoUSB    -> via pyusb, endpoints bulk do EV3 (vendor/product id
#                    conhecidos: 0x0694 / 0x0005)
