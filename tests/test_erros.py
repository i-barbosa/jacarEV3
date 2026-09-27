"""
Testes da hierarquia de erros (jacarev3.erros) e de todo ponto do código
que deveria levantar um erro dela — em vez de KeyError/struct.error/
RuntimeError crus, que não ensinam nada pro aluno.

Sem robô, sem socket de verdade.
"""

import struct

import pytest

from jacarev3 import erros
from jacarev3.robo import RoboEV3


class ConexaoFalsa:
    """Guarda os pacotes em vez de mandar pro robô. `resposta` controla o
    que _enviar(com_resposta=True) recebe de volta."""

    def __init__(self, resposta=b''):
        self.pacotes = []
        self.resposta = resposta
        self._contador = 0

    def proximo_contador(self):
        self._contador += 1
        return self._contador

    def enviar(self, pacote):
        self.pacotes.append(pacote)

    def receber(self, tamanho_max=1024):
        return self.resposta

    def fechar(self):
        pass


@pytest.fixture
def robo():
    return RoboEV3(conexao=ConexaoFalsa())


# ---------------------------------------------------------------- hierarquia


def test_hierarquia_de_classes():
    assert issubclass(erros.ErroDeConexao, erros.ErroJacare)
    assert issubclass(erros.ErroDeConexao, OSError)
    assert issubclass(erros.ErroDeConexaoBluetooth, erros.ErroDeConexao)
    assert issubclass(erros.TempoEsgotado, erros.ErroDeConexao)
    assert issubclass(erros.TempoEsgotado, TimeoutError)
    assert issubclass(erros.ErroNoEV3, erros.ErroDeProtocolo)
    assert issubclass(erros.ErroDeParametro, ValueError)
    assert issubclass(erros.ErroDePorta, erros.ErroDeParametro)
    assert issubclass(erros.ErroDePorta, KeyError)


def test_erro_de_porta_nao_tem_aspas_de_keyerror():
    """KeyError.__str__ normalmente embrulha em repr() — ErroDePorta não
    pode, senão vira 'mensagem' em vez de mensagem."""
    erro = erros.ErroDePorta("Porta de motor inválida: 2.")
    assert str(erro) == "Porta de motor inválida: 2."


def test_codigo_antigo_pegando_keyerror_continua_funcionando(robo):
    """Compatibilidade: quem já tinha `except KeyError` em volta de porta
    errada não pode quebrar com essa mudança."""
    with pytest.raises(KeyError):
        robo.girar_motor(2)


def test_codigo_antigo_pegando_valueerror_continua_funcionando(robo):
    with pytest.raises(ValueError):
        robo.led('roxo')


# ---------------------------------------------------------------- portas


@pytest.mark.parametrize("porta", ['b', 'B'])
def test_porta_motor_aceita_maiuscula_e_minuscula(porta, robo):
    robo.girar_motor(porta, duracao_ms=1)  # não pode levantar


def test_porta_motor_numero_e_recusada_com_dica_de_sensor(robo):
    with pytest.raises(erros.ErroDePorta, match="usa letra"):
        robo.girar_motor(2)


def test_porta_motor_desconhecida_sem_dica_falsa(robo):
    with pytest.raises(erros.ErroDePorta, match="Use 'A', 'B', 'C' ou 'D'"):
        robo.girar_motor('Z')


@pytest.mark.parametrize("porta", ['1', 1])
def test_porta_sensor_aceita_string_e_int(porta, robo):
    robo.conexao.resposta = struct.pack('<HHB', 8, 1, 2) + struct.pack('<f', 42.0)
    from jacarev3 import protocolo as p
    assert robo.ler_sensor(porta, p.MODO_TOQUE) == 42.0


def test_porta_sensor_letra_e_recusada_com_dica_de_motor(robo):
    with pytest.raises(erros.ErroDePorta, match="usa letra"):
        robo.ler_sensor('A', 0)


def test_porta_sensor_desconhecida_sem_dica_falsa(robo):
    with pytest.raises(erros.ErroDePorta, match="Use 1, 2, 3 ou 4"):
        robo.ler_sensor(9, 0)


def test_indice_motor_usa_mesma_validacao_que_porta_motor(robo):
    with pytest.raises(erros.ErroDePorta):
        robo.ler_graus_motor('Z')


# ---------------------------------------------------------------- parâmetros


@pytest.mark.parametrize("metodo,kwargs", [
    ("girar_motor", {"porta": 'B', "velocidade": 200}),
    ("girar_motor", {"porta": 'B', "velocidade": -101}),
    ("mover_continuo", {"porta": 'B', "velocidade": 101}),
    ("girar_motor_graus", {"porta": 'B', "graus": 90, "velocidade": 150}),
    ("mover_base", {"velocidade": -200}),
    ("mover_base_graus", {"graus": 90, "velocidade": 200}),
])
def test_velocidade_fora_da_faixa_e_recusada(robo, metodo, kwargs):
    """Antes disso, isso batia direto no struct.pack('<b', ...) e virava
    struct.error cru."""
    with pytest.raises(erros.ErroDeParametro, match="fora da faixa -100 a 100"):
        getattr(robo, metodo)(**kwargs)


@pytest.mark.parametrize("velocidade", [-100, -1, 0, 1, 100])
def test_velocidade_no_limite_e_aceita(robo, velocidade):
    robo.girar_motor('B', velocidade=velocidade, duracao_ms=1)  # não pode levantar


def test_graus_negativo_e_recusado(robo):
    with pytest.raises(erros.ErroDeParametro, match="graus deve ser positivo"):
        robo.girar_motor_graus('B', graus=-90)


def test_direcao_fora_do_limite_e_recusada(robo):
    with pytest.raises(erros.ErroDeParametro, match=r"-200 e 200"):
        robo.mover_base(direcao=999)


def test_base_com_porta_invalida_e_recusada():
    with pytest.raises(erros.ErroDePorta):
        RoboEV3(conexao=ConexaoFalsa(), base=('Z', 'C'))


def test_base_com_motores_iguais_e_recusada():
    with pytest.raises(erros.ErroDeParametro, match="dois motores diferentes"):
        RoboEV3(conexao=ConexaoFalsa(), base=('b', 'B'))  # mesma porta, case diferente


def test_tipo_de_sensor_invalido_em_portas_e_recusado():
    robo = RoboEV3(conexao=ConexaoFalsa(), portas={1: ('x', 'giroscopio')})
    with pytest.raises(erros.ErroDeParametro):
        robo._tipo_sensor_configurado(1)


def test_construtor_sem_mac_nem_conexao_e_recusado():
    with pytest.raises(erros.ErroDeParametro):
        RoboEV3()


def test_cor_de_led_desconhecida_e_recusada(robo):
    with pytest.raises(erros.ErroDeParametro, match="Cor de LED desconhecida"):
        robo.led('roxo')


# ---------------------------------------------------------------- protocolo/EV3


def test_ev3_respondendo_erro_vira_erro_no_ev3(robo):
    robo.conexao.resposta = struct.pack('<HHB', 3, 1, 0x04)  # tipo 0x04 = erro
    with pytest.raises(erros.ErroNoEV3):
        robo.ler_graus_motor('B')


def test_resposta_curta_demais_vira_erro_de_protocolo(robo):
    robo.conexao.resposta = b'\x01\x02'  # menos de 5 bytes
    with pytest.raises(erros.ErroDeProtocolo, match="curta demais"):
        robo.ler_graus_motor('B')


# ---------------------------------------------------------------- scan não engole conexão caída


class ConexaoQueCai:
    """Simula o link caindo no meio de um testar_motores()/testar_sensores().

    Levanta no enviar() (não no receber()) de propósito: comandos de
    motor são "dispara e esquece" (com_resposta=False), então é o
    enviar() que dispara primeiro nesse caminho — igual à
    ConexaoBluetooth.enviar() de verdade, que já propaga
    ErroDeConexaoBluetooth quando o sendall() falha.
    """

    def proximo_contador(self):
        return 1

    def enviar(self, pacote):
        raise erros.ErroDeConexaoBluetooth("conexão caiu")

    def receber(self, tamanho_max=1024):
        raise erros.ErroDeConexaoBluetooth("conexão caiu")

    def fechar(self):
        pass


def test_testar_motores_nao_engole_queda_de_conexao():
    """Antes, o `except Exception` genérico reportava isso como
    '[AVISO] Sem motor' — uma queda de Bluetooth é bem mais grave que um
    motor ausente, e precisa parar o scan, não esconder o problema."""
    robo = RoboEV3(conexao=ConexaoQueCai())
    with pytest.raises(erros.ErroDeConexaoBluetooth):
        robo.testar_motores()


def test_testar_sensores_nao_engole_queda_de_conexao():
    robo = RoboEV3(conexao=ConexaoQueCai())
    with pytest.raises(erros.ErroDeConexaoBluetooth):
        robo.testar_sensores()
