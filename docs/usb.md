# Conectar por USB

## 1. Conceito

Bluetooth exige parear cada EV3 nas configurações do sistema antes de
usar — em sala de aula, com vários robôs e vários computadores, isso
vira fricção. USB é plugar o cabo e pronto.

O EV3 aparece como um dispositivo **HID** USB comum (a mesma categoria
de mouse e teclado) — não precisa instalar driver nenhum em
Windows/Linux/macOS, porque o sistema já sabe falar com dispositivos
HID nativamente.

!!! warning "Por que não `pyusb`"
    Existem duas formas de falar USB em Python: `pyusb` (via libusb) e
    `hidapi` (via a pilha HID nativa do sistema). `jacarev3` usa
    **hidapi** de propósito. `pyusb` no Windows exigiria trocar o
    driver do EV3 por WinUSB usando uma ferramenta tipo
    [Zadig](https://zadig.akeo.ie/) — precisa de admin, por dispositivo,
    por computador. Numa sala com 20+ máquinas isso é pior que parear
    Bluetooth. `hidapi` não precisa de nada disso.

## 2. Peças que você precisa

- Um cabo USB (o mesmo Mini-USB que carrega o EV3 já serve)
- `pip install jacarev3[usb]` — `hidapi` não é dependência da lib, só
  entra se você for usar esse transporte

## 3. Construindo passo a passo

### Passo 1 — Conectar

```python
from jacarev3 import RoboEV3
from jacarev3.conexao import ConexaoUSB

with RoboEV3(conexao=ConexaoUSB()) as robo:
    robo.apitar()
    robo.led('VERDE')
```

Sem `serie=`, conecta no primeiro EV3 que achar plugado. Com mais de um
robô no mesmo computador, especifica qual:

```python
ConexaoUSB(serie="00160... ")  # número de série do EV3 específico
```

### Passo 2 — O resto da lib nem percebe a diferença

Todo o resto — `girar_motor`, `ler_sensor`, `jacarev3.topicos`, o
[controle remoto](controle.md) — funciona idêntico, porque o protocolo
por cima do fio é exatamente o mesmo do Bluetooth. Só a entrega física
muda; `RoboEV3` não sabe (nem precisa saber) qual transporte tá por
baixo.

## 4. Função pronta da lib

`jacarev3.conexao.ConexaoUSB` já é a peça pronta — não tem "tópico"
separado, é só passar ela em `conexao=` no lugar do MAC do Bluetooth.

## 5. Pra ir além

!!! danger "Ainda não testado em hardware físico"
    `ConexaoUSB` foi implementado a partir de documentação pública e de
    duas implementações de referência independentes já testadas em
    EV3 real (BrianPeek/legoev3 em C#, ChristophGaukel/ev3-python3 em
    Python) — mas **ainda não foi validado com um EV3 físico por USB
    nessa lib**. Se você testar, [abre uma issue](https://github.com/i-barbosa/jacarEV3/issues)
    contando o que aconteceu — bom ou ruim.

- Testa com mais de um EV3 no mesmo computador, usando `serie=` pra
  escolher qual
- Compara a latência de comando (tempo entre mandar e o motor reagir)
  entre USB e Bluetooth no seu setup
