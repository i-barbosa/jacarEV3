"""
Testes do transporte USB (ConexaoUSB): o formato do relatório HID —
byte de report ID, preenchimento até 1024 bytes, e o campo de tamanho
deslocado por causa desse byte extra.

Sem controle físico nem `hidapi` instalado — usa um dispositivo HID
falso, injetado do mesmo jeito que `FontePygame(pygame=...)`.
"""

import struct

import pytest

from jacarev3 import protocolo as p
from jacarev3.conexao import PID_EV3, TAMANHO_RELATORIO_USB, VID_LEGO, ConexaoUSB
from jacarev3.erros import ErroDeConexaoUSB, TempoEsgotado


class DispositivoHidFalso:
    """Substitui um hid.device() — sem controle físico plugado."""

    def __init__(self, resposta=b''):
        self.escritos = []
        self.resposta = resposta
        self.aberto_com = None
        self.fechado = False
        self.timeout_pedido = None

    def open(self, vid, pid, serie=None):
        self.aberto_com = (vid, pid, serie)

    def write(self, relatorio):
        self.escritos.append(bytes(relatorio))

    def read(self, tamanho, timeout_ms):
        self.timeout_pedido = timeout_ms
        return list(self.resposta)  # hidapi devolve lista de ints

    def close(self):
        self.fechado = True


class DispositivoQueNaoAbre:
    def open(self, vid, pid, serie=None):
        raise OSError("dispositivo não encontrado")


class HidFalso:
    """Substitui o módulo `hid` (pacote hidapi) inteiro."""

    def __init__(self, dispositivo=None):
        self._dispositivo = dispositivo if dispositivo is not None else DispositivoHidFalso()

    def device(self):
        return self._dispositivo


def _relatorio_de_resposta(payload_com_ok: bytes) -> bytes:
    """Monta um relatório HID de resposta a partir de um frame de
    Direct Command já pronto (o mesmo formato que ConexaoBluetooth
    recebe) — prefixa o byte de report ID e preenche até 1024."""
    relatorio = bytes([0]) + payload_com_ok
    return relatorio + bytes(TAMANHO_RELATORIO_USB - len(relatorio))


# ---------------------------------------------------------------- conectar


def test_usb_abre_com_vid_pid_padrao():
    dispositivo = DispositivoHidFalso()
    ConexaoUSB(modulo_hid=HidFalso(dispositivo))
    assert dispositivo.aberto_com == (VID_LEGO, PID_EV3, None)


def test_usb_abre_com_serie_especifico():
    dispositivo = DispositivoHidFalso()
    ConexaoUSB(serie="ABC123", modulo_hid=HidFalso(dispositivo))
    assert dispositivo.aberto_com == (VID_LEGO, PID_EV3, "ABC123")


def test_usb_dispositivo_nao_encontrado_vira_erro():
    with pytest.raises(ErroDeConexaoUSB):
        ConexaoUSB(modulo_hid=HidFalso(DispositivoQueNaoAbre()))


# ---------------------------------------------------------------- enviar


def test_usb_enviar_prefixa_report_id_e_preenche_ate_1024():
    dispositivo = DispositivoHidFalso()
    conexao = ConexaoUSB(modulo_hid=HidFalso(dispositivo))

    pacote = p.Comando().add(p.opSOUND, p.SOUND_BREAK).montar(1)
    conexao.enviar(pacote)

    relatorio = dispositivo.escritos[-1]
    assert len(relatorio) == TAMANHO_RELATORIO_USB
    assert relatorio[0] == 0                       # report ID
    assert relatorio[1:1 + len(pacote)] == pacote   # frame intacto
    assert relatorio[1 + len(pacote):] == bytes(TAMANHO_RELATORIO_USB - 1 - len(pacote))


def test_usb_enviar_recusa_pacote_grande_demais():
    conexao = ConexaoUSB(modulo_hid=HidFalso())
    pacote_gigante = bytes(TAMANHO_RELATORIO_USB)  # +1 do report ID já estoura
    with pytest.raises(ErroDeConexaoUSB, match="grande demais"):
        conexao.enviar(pacote_gigante)


# ---------------------------------------------------------------- receber


def test_usb_receber_remonta_o_frame_original():
    # Uma resposta de verdade: contador=1, tipo OK, payload de 4 bytes.
    payload = struct.pack('<f', 42.0)
    corpo = bytes([p.DIRECT_REPLY_OK]) + payload
    frame = struct.pack('<HH', 2 + len(corpo), 1) + corpo

    dispositivo = DispositivoHidFalso(resposta=_relatorio_de_resposta(frame))
    conexao = ConexaoUSB(modulo_hid=HidFalso(dispositivo))

    dados = conexao.receber()
    assert dados == frame

    contador, ok, payload_lido = p.parse_resposta(dados)
    assert (contador, ok) == (1, True)
    assert struct.unpack('<f', payload_lido)[0] == 42.0


def test_usb_receber_relatorio_vazio_vira_tempo_esgotado():
    conexao = ConexaoUSB(modulo_hid=HidFalso(DispositivoHidFalso(resposta=b'')))
    with pytest.raises(TempoEsgotado):
        conexao.receber()


def test_usb_receber_passa_timeout_configurado():
    dispositivo = DispositivoHidFalso(resposta=_relatorio_de_resposta(b'\x05\x00\x01\x00\x02'))
    conexao = ConexaoUSB(timeout=3, modulo_hid=HidFalso(dispositivo))
    conexao.receber()
    assert dispositivo.timeout_pedido == 3000


# ---------------------------------------------------------------- fechar


def test_usb_fechar_chama_close_do_dispositivo():
    dispositivo = DispositivoHidFalso()
    conexao = ConexaoUSB(modulo_hid=HidFalso(dispositivo))
    conexao.fechar()
    assert dispositivo.fechado is True


def test_usb_e_gerenciador_de_contexto():
    dispositivo = DispositivoHidFalso()
    with ConexaoUSB(modulo_hid=HidFalso(dispositivo)):
        assert dispositivo.fechado is False
    assert dispositivo.fechado is True


# ---------------------------------------------------------------- ponta a ponta


def test_robo_por_usb_manda_comando_com_framing_correto():
    """RoboEV3 inteiro, plugado num transporte USB falso — prova que o
    framing extra (report ID + padding) é invisível pro resto da lib."""
    from jacarev3.robo import RoboEV3

    dispositivo = DispositivoHidFalso()
    with RoboEV3(conexao=ConexaoUSB(modulo_hid=HidFalso(dispositivo))) as robo:
        robo.led('VERDE')

    relatorio = dispositivo.escritos[-1]
    assert len(relatorio) == TAMANHO_RELATORIO_USB
    assert relatorio[0] == 0
    # o mesmo bytecode que ConexaoBluetooth receberia, só que 1 byte à frente
    assert bytes([p.opUI_WRITE, p.UI_WRITE_LED, p.lc0(p.LED_VERDE)[0]]) in relatorio
    assert dispositivo.fechado is True
