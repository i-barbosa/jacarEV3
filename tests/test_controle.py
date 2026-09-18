"""
Testes do controle remoto: o loop e as fontes de comando.

Sem robô, sem teclado, sem rede — fonte e robô são dublês. O que está
sendo travado aqui é o comportamento de segurança: se o comando para de
chegar, o robô tem que parar.
"""

import pytest

from jacarev3.fontes import SAIR, FonteUDP
from jacarev3.topicos import controle


class RoboFalso:
    """Anota o que mandaram ele fazer."""

    def __init__(self):
        self.chamadas = []

    def mover_base(self, velocidade=30, direcao=0, duracao_ms=500, frear=False):
        self.chamadas.append(("mover", velocidade, direcao))

    def parar_base(self, frear=True):
        self.chamadas.append(("parar",))

    @property
    def movimentos(self):
        return [c for c in self.chamadas if c[0] == "mover"]


class FonteRoteiro:
    """Devolve uma leitura por chamada, seguindo um roteiro."""

    def __init__(self, roteiro):
        self.roteiro = list(roteiro)
        self.entrou = False
        self.saiu = False

    def __enter__(self):
        self.entrou = True
        return self

    def __exit__(self, *exc):
        self.saiu = True
        return False

    def ler(self):
        if not self.roteiro:
            return SAIR
        return self.roteiro.pop(0)


def rodar(robo, roteiro, **kwargs):
    fonte = FonteRoteiro(roteiro)
    opcoes = dict(intervalo=0, expira=10, velocidade=50, giro=100)
    opcoes.update(kwargs)
    controle.controle_remoto(robo, fonte=fonte, **opcoes)
    return fonte


# ---------------------------------------------------------------- loop


def test_comando_vira_movimento():
    robo = RoboFalso()
    rodar(robo, [(1, 0)])
    assert ("mover", 50, 0) in robo.movimentos


def test_fatores_multiplicam_velocidade_e_giro():
    robo = RoboFalso()
    rodar(robo, [(-1, 1)], velocidade=40, giro=200)
    assert ("mover", -40, 200) in robo.movimentos


def test_zero_zero_para_em_vez_de_mover():
    robo = RoboFalso()
    rodar(robo, [(0, 0)])
    assert robo.movimentos == []
    assert ("parar",) in robo.chamadas


def test_sai_quando_a_fonte_pede():
    robo = RoboFalso()
    fonte = rodar(robo, [SAIR])
    assert fonte.saiu is True


def test_sempre_para_o_robo_no_fim():
    robo = RoboFalso()
    rodar(robo, [(1, 0)])
    assert robo.chamadas[-1] == ("parar",)


def test_fonte_e_usada_como_contexto():
    """O with é quem desmonta terminal cru e socket — não pode ser pulado."""
    robo = RoboFalso()
    fonte = rodar(robo, [(1, 0)])
    assert (fonte.entrou, fonte.saiu) == (True, True)


def test_silencio_da_fonte_para_o_robo():
    """
    O comportamento de segurança: sem notícia por mais que `expira`, o
    robô para, mesmo que o último comando tenha sido "anda".
    """
    robo = RoboFalso()
    rodar(robo, [(1, 0)] + [None] * 30, expira=0.0)

    assert ("parar",) in robo.chamadas
    assert robo.chamadas[-1] == ("parar",)


def test_intervalo_maior_que_a_janela_e_recusado():
    """Renovar depois do prazo vencer faz o robô andar aos trancos."""
    with pytest.raises(ValueError):
        controle.controle_remoto(RoboFalso(), fonte=FonteRoteiro([]),
                                 janela_ms=200, intervalo=0.5)


def test_velocidade_invalida_e_recusada():
    with pytest.raises(ValueError):
        controle.controle_remoto(RoboFalso(), fonte=FonteRoteiro([]), velocidade=0)


# ---------------------------------------------------------------- FonteUDP


@pytest.mark.parametrize("pacote,esperado", [
    (b"1 0", (1.0, 0.0)),
    (b"-1 1", (-1.0, 1.0)),
    (b"0 0\n", (0.0, 0.0)),
    (b"0.5 -0.5", (0.5, -0.5)),
])
def test_udp_interpreta_pacote_valido(pacote, esperado):
    assert FonteUDP._interpretar(pacote) == esperado


@pytest.mark.parametrize("lixo", [b"", b"oi", b"1", b"\xff\xfe", b"a b"])
def test_udp_ignora_pacote_estranho(lixo):
    """Pacote corrompido vira None: o próximo chega em 50 ms mesmo."""
    assert FonteUDP._interpretar(lixo) is None


def test_udp_limita_valores_fora_da_faixa():
    """Controle mal calibrado não vira velocidade 500."""
    assert FonteUDP._interpretar(b"9 -9") == (1.0, -1.0)
