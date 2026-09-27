"""
jacarev3.transporte
--------------------
Protocolo estrutural (`typing.Protocol`) que descreve o que `RoboEV3`
espera de qualquer transporte — Bluetooth, USB, ou uma dublê de teste.

Não é uma classe base pra herdar: `ConexaoBluetooth`, `ConexaoUSB` e
qualquer fake de teste só precisam *ter* esses métodos, com essa
assinatura — não precisam declarar herança nenhuma. É por isso que
`RoboEV3(conexao=MinhaFake())` já funcionava antes desse tipo existir;
ele só documenta, formalmente, o contrato que já estava implícito.
"""

from __future__ import annotations

from typing import Protocol, runtime_checkable


@runtime_checkable
class Transporte(Protocol):
    """O que `RoboEV3._enviar()` precisa de `self.conexao`."""

    def proximo_contador(self) -> int:
        ...

    def enviar(self, pacote: bytes) -> None:
        ...

    def receber(self, tamanho_max: int = 1024) -> bytes:
        ...

    def fechar(self) -> None:
        ...
