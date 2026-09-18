"""
Testes de encoding: congelam os bytes que a biblioteca coloca no fio.

Não precisa de EV3 ligado. A ideia é poder refatorar protocolo.py e
robo.py sem medo: se um byte mudar de lugar, o teste quebra aqui em vez
de quebrar no meio da oficina.

Rodar:
    pip install pytest
    pytest
"""

import struct

import pytest

from jacarev3 import protocolo as p
from jacarev3.robo import RoboEV3


# ---------------------------------------------------------------- fixtures


class ConexaoFalsa:
    """Guarda os pacotes em vez de mandar pro robô."""

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

    @property
    def ultimo_bytecode(self):
        """Só o bytecode do último pacote, sem os 7 bytes de cabeçalho."""
        return self.pacotes[-1][7:]


@pytest.fixture
def robo():
    return RoboEV3(conexao=ConexaoFalsa())


# ---------------------------------------------------------------- parâmetros


def test_lc0_valor_direto():
    assert p.lc0(5) == b'\x05'
    assert p.lc0(0) == b'\x00'


def test_lc0_negativo_em_complemento_de_dois_de_6_bits():
    assert p.lc0(-1) == b'\x3f'
    assert p.lc0(-32) == b'\x20'


def test_prefixos_dos_encodings_maiores():
    assert p.lc1(100) == b'\x81\x64'
    assert p.lc2(1000) == b'\x82\xe8\x03'
    assert p.lc4(100000) == b'\x83\xa0\x86\x01\x00'


def test_lcs_termina_em_zero():
    assert p.lcs("oi") == b'\x84oi\x00'


def test_gv0_marca_variavel_global():
    assert p.gv0(0) == b'\x60'
    assert p.gv0(4) == b'\x64'


@pytest.mark.parametrize("valor,prefixo", [
    (0, b''), (31, b''), (-32, b''),
    (100, b'\x81'), (-100, b'\x81'),
    (1000, b'\x82'), (-1000, b'\x82'),
    (100000, b'\x83'),
])
def test_lc_auto_escolhe_o_menor_encoding(valor, prefixo):
    codificado = p.lc_auto(valor)
    if prefixo:
        assert codificado[:1] == prefixo
    else:
        assert len(codificado) == 1


# ---------------------------------------------------------------- pacote


def test_cabecalho_do_pacote():
    pacote = p.Comando().add(p.opSOUND, p.SOUND_BREAK).montar(42)
    tamanho, contador = struct.unpack('<HH', pacote[:4])

    assert tamanho == len(pacote) - 2      # o campo não conta a si mesmo
    assert contador == 42
    assert pacote[4] == p.DIRECT_COMMAND_NO_REPLY
    assert pacote[5:7] == b'\x00\x00'      # nenhuma variável global alocada


def test_pacote_com_resposta_aloca_globais():
    pacote = p.Comando().add(p.opOUTPUT_GET_COUNT).montar(
        1, com_resposta=True, bytes_globais=4
    )
    assert pacote[4] == p.DIRECT_COMMAND_REPLY
    assert pacote[5:7] == b'\x04\x00'


def test_alocacao_de_globais_passa_de_255_bytes():
    pacote = p.Comando().montar(1, com_resposta=True, bytes_globais=300)
    assert pacote[5:7] == bytes([300 & 0xFF, 300 >> 8])


def test_parse_resposta_ok():
    payload = struct.pack('<i', -720)
    resposta = struct.pack('<HHB', 3 + len(payload), 7, p.DIRECT_REPLY_OK) + payload
    contador, ok, devolvido = p.parse_resposta(resposta)

    assert (contador, ok) == (7, True)
    assert p.ler_int32(devolvido) == -720


def test_parse_resposta_marca_erro():
    resposta = struct.pack('<HHB', 3, 7, p.DIRECT_REPLY_ERROR)
    _, ok, _ = p.parse_resposta(resposta)
    assert ok is False


# ---------------------------------------------------------------- motores


def test_girar_motor_graus_monta_step_speed(robo):
    robo.girar_motor_graus('B', graus=360, velocidade=50, esperar=False)

    assert robo.conexao.ultimo_bytecode == (
        bytes([p.opOUTPUT_STEP_SPEED])
        + p.lc0(0)               # layer
        + p.lc0(p.PORTA_B)       # porta B = 0x02
        + p.lc1(50)              # velocidade
        + p.lc0(0)               # rampa de subida
        + p.lc2(360)             # graus
        + p.lc0(0)               # rampa de descida
        + p.lc0(p.PARAR_BRAKE)
    )


def test_girar_motor_voltas_vira_graus(robo):
    robo.girar_motor_voltas('B', 2, esperar=False)
    assert p.lc2(720) in robo.conexao.ultimo_bytecode


def test_graus_negativo_e_recusado(robo):
    with pytest.raises(ValueError):
        robo.girar_motor_graus('B', graus=-90)


def test_mover_continuo_usa_speed_mais_start(robo):
    robo.mover_continuo('C', velocidade=-40)

    assert robo.conexao.ultimo_bytecode == (
        bytes([p.opOUTPUT_SPEED]) + p.lc0(0) + p.lc0(p.PORTA_C) + p.lc1(-40)
        + bytes([p.opOUTPUT_START]) + p.lc0(0) + p.lc0(p.PORTA_C)
    )


def test_ler_graus_motor_usa_indice_e_nao_bitmask(robo):
    """O firmware indexa pMotor[No] direto, então C é 2 e não 0x04."""
    robo.conexao.resposta = struct.pack('<HHB', 7, 1, p.DIRECT_REPLY_OK) + struct.pack('<i', 123)
    assert robo.ler_graus_motor('C') == 123
    assert robo.conexao.ultimo_bytecode == (
        bytes([p.opOUTPUT_GET_COUNT]) + p.lc0(0) + p.lc0(2) + p.gv0(0)
    )


def test_zerar_graus_motor_usa_bitmask(robo):
    robo.zerar_graus_motor('C')
    assert robo.conexao.ultimo_bytecode == (
        bytes([p.opOUTPUT_CLR_COUNT]) + p.lc0(0) + p.lc0(p.PORTA_C)
    )


# ---------------------------------------------------------------- base motriz


def test_mover_base_junta_os_dois_motores(robo):
    robo.mover_base(velocidade=30, direcao=0, duracao_ms=400)

    assert robo.conexao.ultimo_bytecode == (
        bytes([p.opOUTPUT_TIME_SYNC])
        + p.lc0(0)
        + p.lc0(p.PORTA_B | p.PORTA_C)   # 0x06
        + p.lc1(30)
        + p.lc0(0)                       # reto
        + p.lc2(400)                     # janela do watchdog
        + p.lc0(p.PARAR_COAST)
    )


def test_base_montada_ao_contrario_inverte_a_direcao():
    """
    O firmware sempre chama de "esquerdo" o motor de porta mais baixa.
    Com a base invertida (esquerda em C), o sinal do turn ratio precisa
    virar, senão apertar 'direita' manda o robô pra esquerda.
    """
    normal = RoboEV3(conexao=ConexaoFalsa(), base=('B', 'C'))
    invertida = RoboEV3(conexao=ConexaoFalsa(), base=('C', 'B'))

    normal.mover_base(direcao=100)
    invertida.mover_base(direcao=100)

    assert p.lc1(100) in normal.conexao.ultimo_bytecode
    assert p.lc1(-100) in invertida.conexao.ultimo_bytecode


def test_direcao_fora_do_limite_e_recusada(robo):
    with pytest.raises(ValueError):
        robo.mover_base(direcao=250)


def test_base_precisa_de_dois_motores_diferentes():
    with pytest.raises(ValueError):
        RoboEV3(conexao=ConexaoFalsa(), base=('B', 'B'))


def test_parar_base_para_os_dois(robo):
    robo.parar_base(frear=True)
    assert robo.conexao.ultimo_bytecode == (
        bytes([p.opOUTPUT_STOP]) + p.lc0(0)
        + p.lc0(p.PORTA_B | p.PORTA_C) + p.lc0(p.PARAR_BRAKE)
    )
