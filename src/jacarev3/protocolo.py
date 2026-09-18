"""
jacarev3.protocolo
-----------------
Implementação própria do protocolo "Direct Commands" do EV3, escrita do zero
a partir de duas fontes públicas e oficiais da LEGO:

  1. "LEGO MINDSTORMS EV3 Communication Developer Kit" (PDF oficial da LEGO,
     documenta o formato dos pacotes e dá exemplos de bytes reais).
  2. bytecodes.h — cabeçalho oficial do firmware EV3, publicado pela LEGO em
     github.com/mindboards/ev3sources (lista os opcodes da VM).

Não copia código de nenhuma lib de terceiro (como o ev3_dc, que é GPLv3) —
só reimplementa o protocolo público documentado pela própria fabricante,
do mesmo jeito que dezenas de outras libs independentes (ev3dev-lang-python,
Rust ev3-dc, etc.) já fizeram, cada uma com sua própria licença.

Formato de um Direct Command (confirmado byte a byte no PDF oficial):
  byte 0-1: tamanho do comando (little endian, sem contar esses 2 bytes)
  byte 2-3: contador de mensagem (little endian)
  byte 4:   tipo (0x00 = com resposta, 0x80 = sem resposta)
  byte 5-6: alocação de variáveis globais/locais (empacotado)
  byte 7+:  bytecode do comando

Resposta:
  byte 0-1: tamanho (LE)
  byte 2-3: contador (LE, igual ao do comando)
  byte 4:   tipo (0x02 = OK, 0x04 = erro)
  byte 5+:  buffer de variáveis globais (o que você pediu pra devolver)
"""

import struct

DIRECT_COMMAND_REPLY = 0x00
DIRECT_COMMAND_NO_REPLY = 0x80
DIRECT_REPLY_OK = 0x02
DIRECT_REPLY_ERROR = 0x04


# ---------- Codificação de parâmetros (primitivos LC/GV) ----------
# Confirmado no PDF oficial: LC0 = valor direto (1 byte), LC1 = prefixo 0x81 +
# 1 byte, LC2 = prefixo 0x82 + 2 bytes LE, LC4 = prefixo 0x83 + 4 bytes LE,
# LCS = prefixo 0x84 + string terminada em zero.
# GV0 (variável global curta) = 0x60 | índice — confirmado batendo com os
# bytes de exemplo do PDF (leitura de sensor devolvendo em GV0(0) = byte 0x60).

def lc0(v):
    return bytes([v & 0x3F])


def lc1(v):
    return bytes([0x81]) + struct.pack('<b', v)


def lc2(v):
    return bytes([0x82]) + struct.pack('<h', v)


def lc4(v):
    return bytes([0x83]) + struct.pack('<i', v)


def lcs(texto):
    return bytes([0x84]) + texto.encode('ascii') + b'\x00'


def gv0(indice):
    return bytes([0x60 | (indice & 0x1F)])


def lc_auto(v):
    """Escolhe automaticamente o menor encoding que cabe o valor."""
    if -32 <= v <= 31:
        return lc0(v)
    if -128 <= v <= 127:
        return lc1(v)
    if -32768 <= v <= 32767:
        return lc2(v)
    return lc4(v)


# ---------- Opcodes (de bytecodes.h, header oficial da LEGO) ----------

opSOUND = 0x94
opUI_WRITE = 0x82
opINPUT_DEVICE = 0x99

opOUTPUT_RESET = 0xA2
opOUTPUT_STOP = 0xA3
opOUTPUT_POWER = 0xA4
opOUTPUT_SPEED = 0xA5
opOUTPUT_START = 0xA6
opOUTPUT_POLARITY = 0xA7
opOUTPUT_READ = 0xA8
opOUTPUT_TEST = 0xA9
opOUTPUT_READY = 0xAA
opOUTPUT_STEP_POWER = 0xAC
opOUTPUT_TIME_POWER = 0xAD
opOUTPUT_STEP_SPEED = 0xAE
opOUTPUT_TIME_SPEED = 0xAF
opOUTPUT_STEP_SYNC = 0xB0
opOUTPUT_TIME_SYNC = 0xB1
opOUTPUT_CLR_COUNT = 0xB2
opOUTPUT_GET_COUNT = 0xB3

# Sub-códigos de opSOUND
SOUND_BREAK = 0
SOUND_TONE = 1

# Sub-código de opUI_WRITE
UI_WRITE_LED = 27

# Sub-códigos de opINPUT_DEVICE
INPUT_READY_RAW = 28
INPUT_READY_SI = 29
INPUT_CLR_CHANGES = 26

# Portas de motor (bitmask, confirmado nos bytes de exemplo do PDF)
PORTA_A = 0x01
PORTA_B = 0x02
PORTA_C = 0x04
PORTA_D = 0x08

# Índice da porta de motor (0-3). Alguns opcodes querem o índice, não o
# bitmask: opOUTPUT_GET_COUNT indexa pMotor[No] direto no firmware, mesmo
# a documentação chamando o parâmetro de "bit field".
INDICE_A = 0
INDICE_B = 1
INDICE_C = 2
INDICE_D = 3

# Ação de parada de motor
PARAR_COAST = 0
PARAR_BRAKE = 1

# Limites do "turn ratio" dos comandos sincronizados (c_output.c):
#   0    = reto
#   -100 = para o motor da esquerda (curva fechada pra esquerda)
#   +100 = para o motor da direita
#   ±200 = motores em sentidos opostos (gira no próprio eixo)
TURN_MIN = -200
TURN_MAX = 200

# Cores de LED (0-9, da UI_WRITE_SUBCODE)
LED_PRETO = 0
LED_VERDE = 1
LED_VERMELHO = 2
LED_AMBAR = 3
LED_VERDE_PISCA = 4
LED_VERMELHO_PISCA = 5
LED_AMBAR_PISCA = 6
LED_VERDE_PULSA = 7
LED_VERMELHO_PULSA = 8
LED_AMBAR_PULSA = 9

# Modos de sensor mais usados (públicos, mesmos valores usados por
# ev3dev/ev3-g e outras implementações independentes)
MODO_TOQUE = 0            # 0 = solto, 1 = pressionado
MODO_ULTRASSONICO_CM = 0  # distância em cm
MODO_COR_REFLETIDA = 0
MODO_COR_AMBIENTE = 1
MODO_COR_COR = 2          # 0-7: nenhuma, preto, azul, verde, amarelo, vermelho, branco, marrom


class Comando:
    """Monta um Direct Command byte a byte."""

    def __init__(self):
        self.bytecode = b''

    def add(self, *partes):
        for p in partes:
            self.bytecode += p if isinstance(p, (bytes, bytearray)) else bytes([p])
        return self

    def montar(self, contador, com_resposta=False, bytes_globais=0):
        tipo = DIRECT_COMMAND_REPLY if com_resposta else DIRECT_COMMAND_NO_REPLY
        # aloca variáveis globais: 10 bits, byte5 = bits baixos, byte6 bits 0-1 = bits altos
        header_vars = bytes([
            bytes_globais & 0xFF,
            (bytes_globais >> 8) & 0x03,
        ])
        corpo = bytes([tipo]) + header_vars + self.bytecode
        # "tamanho" no protocolo EV3 conta o contador (2 bytes) + corpo,
        # excluindo só os 2 bytes do próprio campo de tamanho.
        tamanho = 2 + len(corpo)
        return struct.pack('<HH', tamanho, contador) + corpo


def parse_resposta(dados):
    """Retorna (contador, ok, payload) de uma resposta do EV3."""
    if len(dados) < 5:
        raise ValueError("Resposta curta demais")
    tamanho, contador, tipo = struct.unpack('<HHB', dados[:5])
    ok = (tipo == DIRECT_REPLY_OK)
    payload = dados[5:5 + tamanho - 3]
    return contador, ok, payload


def ler_float(payload, offset=0):
    return struct.unpack_from('<f', payload, offset)[0]


def ler_int32(payload, offset=0):
    """Lê um DATA32 com sinal (contagem de encoder, por exemplo)."""
    return struct.unpack_from('<i', payload, offset)[0]


def ler_int8(payload, offset=0):
    """Lê um DATA8 com sinal (flag de ocupado, por exemplo)."""
    return struct.unpack_from('<b', payload, offset)[0]
