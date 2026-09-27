"""
Testes do controle remoto: o loop e as fontes de comando.

Sem robô, sem teclado, sem rede, sem controle físico nem pygame de
verdade — fonte e robô são dublês. O que está sendo travado aqui é o
comportamento de segurança: se o comando para de chegar, o robô tem que
parar.
"""

import types

import pytest

from jacarev3.fontes import SAIR, FontePygame, FonteUDP
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


# ---------------------------------------------------------------- FontePygame


class JoystickFalso:
    """Substitui um pygame.joystick.Joystick — sem controle físico."""

    def __init__(self, eixos=None, botoes=None):
        self.eixos = dict(eixos or {})
        self.botoes = set(botoes or ())
        self.inicializado = False

    def init(self):
        self.inicializado = True

    def get_axis(self, indice):
        return self.eixos.get(indice, 0.0)

    def get_button(self, indice):
        return indice in self.botoes


class PygameFalso:
    """Substitui o módulo pygame inteiro — sem pygame instalado de verdade."""

    def __init__(self, joystick=None, n_joysticks=1):
        self.chamadas = []
        self._joystick = joystick or JoystickFalso()
        self.joystick = types.SimpleNamespace(
            init=lambda: self.chamadas.append("joystick.init"),
            quit=lambda: self.chamadas.append("joystick.quit"),
            get_count=lambda: n_joysticks,
            Joystick=lambda indice: self._joystick,
        )
        self.event = types.SimpleNamespace(pump=lambda: None)

    def init(self):
        self.chamadas.append("init")

    def quit(self):
        self.chamadas.append("quit")


def test_pygame_gatilhos_viram_frente_e_re():
    joystick = JoystickFalso(eixos={5: 1.0})  # RT no fundo
    with FontePygame(pygame=PygameFalso(joystick), taxa_suavizacao=1) as fonte:
        assert fonte.ler() == (1.0, 0.0)


def test_pygame_normaliza_gatilho_no_estilo_solto_apertado():
    """Alguns drivers reportam o gatilho de -1 (solto) a 1 (fundo)."""
    joystick = JoystickFalso(eixos={4: -1.0})  # LT solto, convenção -1..1
    with FontePygame(pygame=PygameFalso(joystick), taxa_suavizacao=1) as fonte:
        assert fonte.ler() == (0.0, 0.0)


def test_pygame_zona_morta_zera_giro_pequeno():
    joystick = JoystickFalso(eixos={0: 0.05})  # abaixo da zona morta padrão (0.1)
    with FontePygame(pygame=PygameFalso(joystick), taxa_suavizacao=1) as fonte:
        assert fonte.ler() == (0.0, 0.0)


def test_pygame_giro_acima_da_zona_morta_passa_direto():
    joystick = JoystickFalso(eixos={0: 0.5})
    with FontePygame(pygame=PygameFalso(joystick), taxa_suavizacao=1) as fonte:
        assert fonte.ler() == (0.0, 0.5)


def test_pygame_suaviza_a_resposta_ao_longo_do_tempo():
    joystick = JoystickFalso(eixos={5: 1.0})
    with FontePygame(pygame=PygameFalso(joystick), taxa_suavizacao=0.25) as fonte:
        vel1, _ = fonte.ler()
        vel2, _ = fonte.ler()
        assert vel1 == pytest.approx(0.25)
        assert vel2 == pytest.approx(0.4375)
        assert vel1 < vel2 < 1.0


def test_pygame_botao_sair_encerra():
    joystick = JoystickFalso(botoes={0})
    with FontePygame(pygame=PygameFalso(joystick)) as fonte:
        assert fonte.ler() is SAIR


def test_pygame_sem_controle_conectado_recusa():
    with pytest.raises(RuntimeError):
        with FontePygame(pygame=PygameFalso(n_joysticks=0)):
            pass


def test_pygame_entra_e_sai_inicializa_e_desmonta_o_joystick():
    fake = PygameFalso()
    with FontePygame(pygame=fake) as fonte:
        assert fonte._joystick.inicializado is True
    assert "joystick.quit" in fake.chamadas
    assert "quit" in fake.chamadas


class JoystickContador(JoystickFalso):
    """Aperta o botão de sair sozinho depois de `apertar_apos` leituras —
    sem isso o loop de controle_remoto() nunca teria por que parar."""

    def __init__(self, eixos, botao_sair, apertar_apos):
        super().__init__(eixos=eixos)
        self._botao_sair = botao_sair
        self._apertar_apos = apertar_apos
        self._chamadas = 0

    def get_button(self, indice):
        if indice != self._botao_sair:
            return False
        self._chamadas += 1
        return self._chamadas > self._apertar_apos


def test_pygame_plugado_no_loop_de_controle():
    """De ponta a ponta: FontePygame alimentando controle_remoto()."""
    joystick = JoystickContador(
        eixos={5: 1.0, 0: 1.0}, botao_sair=0, apertar_apos=1,
    )  # RT no fundo + giro pra direita, sai na 2ª leitura
    robo = RoboFalso()
    with FontePygame(pygame=PygameFalso(joystick), taxa_suavizacao=1) as fonte:
        controle.controle_remoto(
            robo, fonte=fonte, intervalo=0, expira=10, velocidade=50, giro=100,
        )
    assert ("mover", 50, 100) in robo.movimentos
    assert robo.chamadas[-1] == ("parar",)
