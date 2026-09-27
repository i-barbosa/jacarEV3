"""
jacarev3.erros
--------------
Toda exceção que a lib levanta de propósito passa por aqui. A ideia é
simples: `except jacarev3.erros.ErroJacare` pega qualquer erro nosso,
mas cada subclasse ainda herda da exceção padrão do Python mais parecida
(`ValueError`, `KeyError`, `OSError`, `TimeoutError`) — então código
antigo que já fazia `except ValueError:` em volta de `led()`, por
exemplo, continua funcionando sem mudar nada.

Hierarquia:

    ErroJacare
    ├── ErroDeConexao(..., OSError)        — Bluetooth não conectou/caiu
    │   ├── ErroDeConexaoBluetooth         — especificamente pelo transporte RFCOMM
    │   └── TempoEsgotado(..., TimeoutError)
    ├── ErroDeProtocolo                    — resposta do EV3 não bateu
    │   └── ErroNoEV3                      — o EV3 respondeu "erro" (tipo 0x04)
    └── ErroDeParametro(..., ValueError)   — você passou um valor inválido
        └── ErroDePorta(..., KeyError)     — porta de motor/sensor errada
"""


class ErroJacare(Exception):
    """Base de tudo que essa lib levanta de propósito."""


class ErroDeConexao(ErroJacare, OSError):
    """Não deu pra falar com o EV3: não conectou, ou a conexão caiu no meio."""


class ErroDeConexaoBluetooth(ErroDeConexao):
    """Falha específica do transporte Bluetooth clássico (RFCOMM). Separado
    de ErroDeConexao pra quando WiFi/USB existirem, cada transporte poder
    ter sua própria subclasse sem quebrar quem já pega ErroDeConexao."""


class TempoEsgotado(ErroDeConexao, TimeoutError):
    """Esperou o tempo configurado e não chegou resposta nenhuma."""


class ErroDeProtocolo(ErroJacare):
    """A resposta do EV3 não bateu com o que o protocolo espera (bytes
    curtos demais, corrompidos, ou fora do formato do Direct Command)."""


class ErroNoEV3(ErroDeProtocolo):
    """O EV3 recebeu o comando e respondeu "erro" (tipo 0x04) — geralmente
    modo/porta errada (ex: pedir cor num sensor de toque)."""


class ErroDeParametro(ErroJacare, ValueError):
    """Você passou um valor que a lib não aceita (fora de faixa, opção
    desconhecida, combinação inválida de parâmetros)."""


class ErroDePorta(ErroDeParametro, KeyError):
    """Porta de motor ou sensor que não existe, ou porta do tipo errado
    (letra onde era pra ser número, ou vice-versa)."""

    def __str__(self):
        # KeyError.__str__ embrulha a mensagem em repr() (aspas extras);
        # aqui a mensagem já é a frase inteira, então devolve ela crua.
        return self.args[0] if self.args else super().__str__()
