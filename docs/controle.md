# Controle remoto — teclado ou ESP32

## 1. Conceito

Em vez de o robô decidir sozinho o que fazer (como em
[seguir linha](circuito.md) ou [desviar de obstáculo](desvio.md)), aqui
é você quem dirige, de onde quiser: teclado do computador ou um
controle físico de ESP32 mandando comando pela rede.

A peça central é a **fonte** (`jacarev3.fontes`) — qualquer objeto com
um método `ler()` que devolve o estado atual de velocidade/direção. O
loop de controle não sabe nem se importa de onde vem o comando; trocar
de teclado pra ESP32 é só trocar a fonte.

O outro ponto que importa: **o robô tem que parar sozinho se perder
contato**. Cada comando de movimento tem um prazo curto no próprio EV3
(`opOUTPUT_TIME_SYNC`) — se o script travar, o Bluetooth cair, ou o
controle físico sair do alcance, o EV3 desliga os motores sozinho.
Nenhum controle remoto deve depender de uma mensagem de "parar" que
pode nunca chegar.

## 2. Peças que você precisa

- 2 motores formando a base motriz (por padrão portas `B` e `C`)
- Pra controle por teclado: nada além do computador
- Pra controle por ESP32: uma placa ESP32 com MicroPython, ligada na
  mesma rede Wi-Fi do computador — veja
  [`exemplos/esp32_controle.py`](https://github.com/i-barbosa/jacarEV3/blob/main/exemplos/esp32_controle.py)

## 3. Construindo passo a passo

### Passo 1 — Controle pelo teclado

```python
from jacarev3 import RoboEV3
from jacarev3.topicos import controle

with RoboEV3('00:16:53:64:F8:B8') as robo:
    controle.controle_remoto(robo, verboso=True)
```

Sem `fonte=`, o padrão é o teclado do próprio computador: `W` frente,
`S` ré, `A`/`D` vira, espaço para, `Q` sai. `verboso=True` imprime cada
comando enviado — bom pra entender o que tá acontecendo antes de tirar.

### Passo 2 — Entender o "porquê" da janela de tempo

Repare no parâmetro `janela_ms` (padrão 400ms): é o prazo que cada
comando dá pro EV3 antes de parar sozinho. O loop renova esse prazo a
cada `intervalo` segundos (padrão 0.1s) — bem menor que a janela, senão
o robô fica engasgando entre um comando e outro:

```python
controle.controle_remoto(
    robo,
    velocidade=35,   # velocidade base, 1-100
    giro=100,        # intensidade da curva, 0-200 (200 = gira no lugar)
    janela_ms=400,   # prazo de cada comando no EV3
    intervalo=0.1,   # de quanto em quanto tempo renova
)
```

Testa soltar a tecla e contar quanto tempo até o robô parar — dá pra
sentir o `expira` (padrão 0.25s) na prática.

### Passo 3 — Trocar pra um controle físico (ESP32)

Grava [`exemplos/esp32_controle.py`](https://github.com/i-barbosa/jacarEV3/blob/main/exemplos/esp32_controle.py)
na placa (MicroPython de fábrica, sem biblioteca extra) e ajusta o
Wi-Fi e o IP do computador no topo do arquivo. A placa manda um pacote
UDP de texto (`"<velocidade> <direção>"`) pra porta 9000 sempre que o
estado dos botões muda.

Do lado do Python, troca a fonte:

```python
from jacarev3 import RoboEV3
from jacarev3.fontes import FonteUDP
from jacarev3.topicos import controle

with RoboEV3('00:16:53:64:F8:B8') as robo:
    controle.controle_remoto(robo, fonte=FonteUDP(porta=9000), verboso=True)
```

UDP não garante entrega e não avisa quando a conexão cai — e isso é uma
vantagem aqui: se o controle sumir, os pacotes simplesmente param de
chegar, o `expira` do loop dispara, e o robô para.

### Passo 4 — Escrever sua própria fonte

Qualquer coisa com `ler()` (e `with` opcional) serve — um gamepad, um
sensor de gesto, outro protocolo de rede:

```python
class FonteMinhaIdeia:
    def __enter__(self):
        return self

    def __exit__(self, *exc):
        return False

    def ler(self):
        # devolve None (nada novo), (velocidade, direcao) ou fontes.SAIR
        ...
```

## 4. Função pronta da lib

`jacarev3.topicos.controle.controle_remoto()` já é a função pronta —
não tem uma versão "mais simples" por baixo, ela foi desenhada pra ser
usada direto (veja os passos acima). O que muda de uso pra uso é qual
`fonte=` você passa.

## 5. Pra ir além

- Ajusta `velocidade`/`giro` pro seu robô — motor diferente, peso
  diferente, pista diferente pedem números diferentes
- Combina com [seguir linha](circuito.md): controle manual até achar a
  pista, aí troca pra `circuito.seguir_linha()`
- Escreve uma fonte de gamepad (a maioria expõe eixos analógicos via
  biblioteca própria do SO — dá um `ler()` bem mais suave que WASD)
