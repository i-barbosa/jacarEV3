# Básico — som, LED, motor, sensor

## 1. Conceito

Antes de qualquer lógica de controle, você precisa saber fazer 4 coisas
soltas: tocar som, acender LED, mexer motor, ler sensor. Tudo o resto da
lib (inclusive os tópicos como `circuito` e `desvio`) é só combinação
dessas 4 coisas dentro de um loop.

## 2. Conectando

```python
from jacarev3 import RoboEV3

robo = RoboEV3('00:16:53:64:F8:B8')  # troca pelo MAC do seu EV3
```

O MAC aparece nas configurações Bluetooth do seu PC, depois de parear
com o EV3 uma vez.

## 3. Construindo passo a passo

### Passo 1 — Som (confirma que a conexão funciona)

```python
robo.apitar()
```

Se apitar, a conexão Bluetooth tá ok. Esse é sempre o primeiro teste.

### Passo 2 — LED

```python
robo.led('VERDE')
time.sleep(2)
robo.led('DESLIGADO')
```

### Passo 3 — Motor por tempo

```python
robo.girar_motor('A', velocidade=30, duracao_ms=1000)
```

Motor A gira 1 segundo a 30% de velocidade, e o `girar_motor` já espera
o tempo certo antes de voltar (não precisa de `time.sleep` extra).

### Passo 4 — Motor contínuo (pra loop de controle)

`girar_motor` para sozinho. Mas quando você quer controlar o motor a
cada instante (tipo seguir linha), precisa de um motor que **não** para
sozinho:

```python
robo.mover_continuo('A', velocidade=30)
time.sleep(1)
robo.parar_motor('A')
```

Essa é a peça que os tópicos usam por baixo dos panos.

### Passo 5 — Ler sensor uma vez

```python
from jacarev3 import protocolo as p

distancia = robo.ler_sensor(porta=4, modo=p.MODO_ULTRASSONICO_CM)
print(distancia)
```

Cada tipo de sensor tem um "modo" — é o que diz pro EV3 que tipo de dado
você quer de volta. As constantes já vêm prontas em `jacarev3.protocolo`:

| Constante | Sensor | O que devolve |
|---|---|---|
| `MODO_ULTRASSONICO_CM` | Ultrassônico | distância em cm |
| `MODO_TOQUE` | Toque | 0 (solto) ou 1 (pressionado) |
| `MODO_COR_REFLETIDA` | Cor | % de luz refletida (0-100) |
| `MODO_COR_COR` | Cor | código de cor (0-7) |

### Passo 6 — Ler sensor em loop (a base de tudo)

```python
import time

while True:
    distancia = robo.ler_sensor(porta=4, modo=p.MODO_ULTRASSONICO_CM)
    print(distancia)
    time.sleep(0.1)
```

Esse loop — ler sensor, decidir algo, mexer motor, repetir — é a
estrutura por trás de `seguir_linha()` e `desviar_obstaculo()`. Uma vez
que você entende esse padrão, os tópicos prontos são só "o que fazer
com a leitura" mudando.

## 4. Pra ir além

- Faz um loop que acende o LED verde quando o sensor de toque tá
  pressionado, e vermelho quando solto
- Faz o motor girar mais rápido quanto mais perto um obstáculo tá
  (em vez de só parar)

Tem uma lista de exercícios em 4 níveis de dificuldade, desse módulo
e dos outros, em [Atividades](atividades.md#basico-som-led-motor-sensor).
