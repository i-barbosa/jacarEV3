"""
Controle remoto do jacarEV3 — lado ESP32 (MicroPython).

Lê 4 botões e manda o estado por WiFi, via UDP, pro computador que está
rodando o jacarEV3. Quem fala com o EV3 é o PC; esse aqui é só o controle
na mão.

GRAVAR NO ESP32:
    1. Instala o MicroPython na placa (esptool + firmware do site oficial).
    2. Copia esse arquivo pro ESP32 como main.py:
         pip install mpremote
         mpremote connect COM7 fs cp esp32_controle.py :main.py
    3. Ajusta REDE, SENHA e IP_PC aqui embaixo antes de copiar.
    4. Liga a placa. Com main.py na raiz, ela começa sozinha.

LIGAÇÃO (DevKit V1):
    botão frente    -> GPIO 32  e GND
    botão ré        -> GPIO 33  e GND
    botão esquerda  -> GPIO 25  e GND
    botão direita   -> GPIO 26  e GND

    Sem resistor: o pull-up interno segura o pino em 1, e o botão puxa
    pra 0 quando apertado. Não use GPIO 34 a 39 pra botão — esses pinos
    não têm pull-up interno.

PROTOCOLO:
    Um datagrama de texto a cada ENVIO_MS: "<velocidade> <direcao>"
    Valores de -1 a 1. Exemplos: "1 0" frente, "1 1" direita, "0 0" parado.
    Estado inteiro em cada pacote, então pacote perdido não atrapalha.
"""

import network
import socket
import time
from machine import Pin

# ----------------------------------------------------------- configuração

REDE = "NOME_DA_SUA_REDE"
SENHA = "SENHA_DA_REDE"
IP_PC = "192.168.0.100"    # IP do computador que roda o jacarEV3
PORTA = 9000

ENVIO_MS = 50              # de quanto em quanto tempo manda o estado

PINOS = {
    "frente": 32,
    "re": 33,
    "esquerda": 25,
    "direita": 26,
}

# LED da placa, pra ver se conectou
PINO_LED = 2


# ----------------------------------------------------------- hardware

botoes = {
    nome: Pin(numero, Pin.IN, Pin.PULL_UP)
    for nome, numero in PINOS.items()
}
led = Pin(PINO_LED, Pin.OUT)


def apertado(nome):
    """Pull-up: pino em 0 quer dizer botão apertado."""
    return botoes[nome].value() == 0


def conectar_wifi():
    wlan = network.WLAN(network.STA_IF)
    wlan.active(True)

    if not wlan.isconnected():
        print("Conectando em", REDE)
        wlan.connect(REDE, SENHA)
        for _ in range(60):          # até 30 s esperando
            if wlan.isconnected():
                break
            led.value(not led.value())
            time.sleep(0.5)

    if not wlan.isconnected():
        led.value(0)
        raise RuntimeError("Não conectou no WiFi — confere REDE e SENHA")

    led.value(1)
    print("Conectado. IP do controle:", wlan.ifconfig()[0])
    return wlan


def estado_dos_botoes():
    """Traduz os botões em (velocidade, direcao), cada um de -1 a 1."""
    velocidade = 0
    direcao = 0

    if apertado("frente"):
        velocidade = 1
    elif apertado("re"):
        velocidade = -1

    if apertado("esquerda"):
        direcao = -1
    elif apertado("direita"):
        direcao = 1

    # curva sem frente nem ré: gira no lugar
    if velocidade == 0 and direcao != 0:
        velocidade = 1

    return velocidade, direcao


def main():
    conectar_wifi()
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    destino = (IP_PC, PORTA)
    print("Mandando pra", destino)

    while True:
        velocidade, direcao = estado_dos_botoes()
        mensagem = "{} {}".format(velocidade, direcao)

        try:
            sock.sendto(mensagem.encode(), destino)
        except OSError as erro:
            # rede caiu no meio: não derruba o controle, tenta de novo.
            # O robô para sozinho enquanto os pacotes não chegam.
            print("Falha ao enviar:", erro)
            time.sleep(0.5)

        time.sleep_ms(ENVIO_MS)


main()
