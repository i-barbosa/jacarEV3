# Desvio — desviar de obstáculo

## 1. Conceito

Robô anda reto até o sensor ultrassônico detectar algo perto demais, aí
para, gira pra um lado, e continua andando. É a base de qualquer robô
"explorador" ou labirinto.

## 2. Peças que você precisa

- 1 sensor ultrassônico, apontando pra frente do robô
- 2 motores (esquerda e direita)

## 3. Construindo passo a passo

### Passo 1 — Ver a distância em tempo real

```python
from jacarev3 import RoboEV3, protocolo as p
import time

robo = RoboEV3('00:16:53:64:F8:B8')

while True:
    distancia = robo.ler_sensor(porta=4, modo=p.MODO_ULTRASSONICO_CM)
    print(f"{distancia:.1f} cm")
    time.sleep(0.1)
```

Aproxima a mão do sensor, confirma que o número desce direitinho.
Decide qual distância mínima faz sentido pro seu robô (15cm é um bom
começo).

### Passo 2 — Andar reto

```python
robo.mover_continuo('B', 30)
robo.mover_continuo('C', 30)
```

Confirma que o robô anda reto de verdade — se ele desviar pra um lado
sozinho, os dois motores não tão na mesma velocidade de verdade (ajusta
um dos dois um pouco pra compensar).

### Passo 3 — Parar quando perto

```python
distancia_minima = 15

while True:
    distancia = robo.ler_sensor(porta=4, modo=p.MODO_ULTRASSONICO_CM)

    if distancia is not None and distancia < distancia_minima:
        robo.parar_motor('B')
        robo.parar_motor('C')
        print("Parou!")
        break
    else:
        robo.mover_continuo('B', 30)
        robo.mover_continuo('C', 30)

    time.sleep(0.05)
```

Testa só até aqui primeiro — confirma que ele realmente para antes de
bater.

### Passo 4 — Girar e continuar (em vez de só parar)

```python
import time

distancia_minima = 15
velocidade = 30

try:
    while True:
        distancia = robo.ler_sensor(porta=4, modo=p.MODO_ULTRASSONICO_CM)

        if distancia is not None and distancia < distancia_minima:
            robo.parar_motor('B')
            robo.parar_motor('C')
            time.sleep(0.1)

            # gira no lugar: motores em sentidos opostos
            robo.mover_continuo('B', -velocidade)
            robo.mover_continuo('C', velocidade)
            time.sleep(0.6)  # tempo de giro — ajusta na mão
        else:
            robo.mover_continuo('B', velocidade)
            robo.mover_continuo('C', velocidade)

        time.sleep(0.05)
except KeyboardInterrupt:
    robo.parar_motor('B')
    robo.parar_motor('C')
```

O `time.sleep(0.6)` no giro é a parte mais "artesanal" — não tem como
calcular exato sem encoder de posição, então ajusta na mão testando até
o robô girar mais ou menos 90°.

## 4. Função pronta da lib

```python
from jacarev3 import RoboEV3
from jacarev3.topicos import desvio

with RoboEV3('00:16:53:64:F8:B8') as robo:
    desvio.desviar_obstaculo(robo, porta_sensor=4, verboso=True)
```

## 5. Pra ir além

- Faz o robô escolher o lado do giro baseado em outro sensor (dois
  ultrassônicos, ou um giro-e-mede-de-novo pra ver qual lado tá mais
  livre)
- Troca o "gira tempo fixo" por "gira até o sensor mostrar caminho
  livre de novo"
- Combina com `circuito.seguir_linha()`: segue linha, mas desvia se
  aparecer obstáculo no meio do caminho

Tem uma lista de exercícios em 4 níveis de dificuldade, desse módulo
e dos outros, em [Atividades](atividades.md#desviar-de-obstaculo-desvio).
