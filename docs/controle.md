# Controle remoto — controle de Xbox via pygame

## 1. Conceito

Em vez de o robô decidir sozinho o que fazer (como em
[seguir linha](circuito.md) ou [desviar de obstáculo](desvio.md)), aqui
é você quem dirige, com um controle de Xbox ligado no computador.

A peça central é a **fonte** (`jacarev3.fontes`) — qualquer objeto com
um método `ler()` que devolve o estado atual de velocidade/direção. O
loop de controle (`jacarev3.topicos.controle`) não sabe nem se importa
de onde vem o comando — só entende `(fator_velocidade, fator_giro)`.
`FontePygame` é a fonte que lê o controle físico via
[pygame](https://www.pygame.org/) e devolve isso.

Estilo "carro": os gatilhos **RT/LT** aceleram e dão ré, e o
**analógico esquerdo** faz a curva — em vez do tanque clássico de dois
analógicos.

O outro ponto que importa: **o robô tem que parar sozinho se perder
contato**. Cada comando de movimento tem um prazo curto no próprio EV3
(`opOUTPUT_TIME_SYNC`) — se o script travar ou o Bluetooth cair, o EV3
desliga os motores sozinho. Nenhum controle remoto deve depender de uma
mensagem de "parar" que pode nunca chegar.

## 2. Peças que você precisa

- 2 motores formando a base motriz (por padrão portas `B` e `C`)
- Um controle de Xbox (testado com Xbox 360) ligado no computador —
  com fio ou pelo receptor sem fio
- `pip install jacarev3[pygame]` — `pygame` não é dependência da lib,
  só entra se você for usar essa fonte

## 3. Construindo passo a passo

### Passo 1 — Confirmar que o pygame enxerga o controle

Antes de ligar no robô, confirma que o controle foi detectado e anota
quantos eixos/botões ele tem (o mapeamento de eixo varia por driver):

```python
import pygame

pygame.init()
pygame.joystick.init()

joystick = pygame.joystick.Joystick(0)
joystick.init()
print(f"Controle: {joystick.get_name()}")
print(f"Eixos: {joystick.get_numaxes()} | Botões: {joystick.get_numbuttons()}")
```

Se `pygame.joystick.get_count()` for 0, o controle não foi detectado —
confere o pareamento/fio antes de continuar.

### Passo 2 — Controle pelo `FontePygame`

```python
from jacarev3 import RoboEV3
from jacarev3.fontes import FontePygame
from jacarev3.topicos import controle

with RoboEV3('00:16:53:64:F8:B8') as robo:
    with FontePygame() as fonte:
        controle.controle_remoto(robo, fonte=fonte, verboso=True)
```

Os eixos padrão (`eixo_rt=5`, `eixo_lt=4`, `eixo_giro=0`, `botao_sair=0`)
são os confirmados num Xbox 360 via pygame no Windows. Se o seu
controle mapear diferente (varia por driver/SO), ajusta na hora de
criar a fonte:

```python
FontePygame(eixo_rt=5, eixo_lt=2, eixo_giro=0, botao_sair=1)
```

`verboso=True` imprime cada comando enviado — bom pra confirmar que o
mapeamento de eixo bate antes de tirar.

### Passo 3 — Ajustar a sensação de resposta

Dois parâmetros de `FontePygame` mudam como o controle "sente":

```python
FontePygame(
    zona_morta_giro=0.1,    # abaixo disso, giro vira 0 (evita curva fantasma)
    taxa_suavizacao=0.25,   # 0-1: mais alto = resposta mais direta e brusca
)
```

E `velocidade=`/`giro=` do `controle_remoto()` controlam a escala final
— o quanto o gatilho no fundo e o analógico todo pro lado valem em
velocidade real do motor:

```python
controle.controle_remoto(robo, fonte=fonte, velocidade=50, giro=100)
```

!!! note "Por que a curva não é idêntica a um carro de verdade"
    `FontePygame` só lê o controle e devolve `(velocidade, giro)` — quem
    mistura isso nas duas rodas é o `mover_base()` da lib, usando o
    turn ratio nativo do firmware do EV3 (o mesmo usado por
    [seguir linha](circuito.md) e [desviar de obstáculo](desvio.md)).
    Não é uma mistura por roda calculada à mão — se a curva estiver
    mole ou brusca demais, ajusta `giro=` em vez do código da fonte.

## 4. Função pronta da lib

`jacarev3.topicos.controle.controle_remoto()` já é a função pronta —
o que muda de uso pra uso é qual `fonte=` você passa. Sem `fonte=`, o
padrão é o teclado do computador (`W`/`S`/`A`/`D`, espaço pra parar,
`Q` pra sair) — útil pra testar rápido sem controle físico em mãos.

## 5. Pra ir além

- Ajusta `velocidade=`/`giro=` pro seu robô — motor diferente, peso
  diferente pedem números diferentes
- Combina com [seguir linha](circuito.md): dirige manualmente até achar
  a pista, aí troca pra `circuito.seguir_linha()`
- Existe também `jacarev3.fontes.FonteUDP`, pra um controle físico
  externo (ex: um ESP32) mandando comando pela rede — ainda não é o
  fluxo que a gente usa em produção, mas o `exemplos/esp32_controle.py`
  no repositório mostra como ligar

Tem uma lista de exercícios em 4 níveis de dificuldade, desse módulo
e dos outros, em [Atividades](atividades.md#controle-remoto-controle).
