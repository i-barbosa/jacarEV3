# Circuito — seguir linha preta

## 1. Conceito

Tarefa clássica de robótica: um robô com sensor de cor apontando pro
chão precisa seguir uma linha preta (ou branca) desenhada no chão.

A ideia central: o sensor de cor em **modo refletância** devolve um
número de 0 a 100 — quanto mais escuro embaixo dele, menor o número.
O robô fica "testando" se tá em cima do claro ou do escuro, e corrige a
direção a cada leitura. Isso é chamado de controle **bang-bang** (só
duas ações possíveis: vira pra um lado ou pro outro — sem meio termo).

## 2. Peças que você precisa

- 1 sensor de cor, apontando pro chão, uns 1-2cm de altura
- 2 motores (esquerda e direita) — o robô precisa conseguir girar no
  lugar variando a velocidade de cada roda
- Uma pista com linha preta em fundo claro (ou o contrário — só inverte
  a lógica)

## 3. Construindo passo a passo

### Passo 1 — Ver o que o sensor enxerga

Antes de programar qualquer lógica, você **precisa** saber que números o
seu sensor devolve no seu chão específico (varia com iluminação, cor do
piso, etc):

```python
from jacarev3 import RoboEV3, protocolo as p
import time

robo = RoboEV3('00:16:53:64:F8:B8')

for _ in range(50):
    leitura = robo.ler_sensor(porta=1, modo=p.MODO_COR_REFLETIDA)
    print(leitura)
    time.sleep(0.2)
```

Passa o sensor por cima do fundo claro, anota o número. Passa por cima
da linha preta, anota o número. A média dos dois é o seu **limiar**.

### Passo 2 — Decisão simples (sem motor ainda)

```python
limiar = 50  # troca pelo que você mediu no passo 1

while True:
    leitura = robo.ler_sensor(porta=1, modo=p.MODO_COR_REFLETIDA)
    if leitura > limiar:
        print("CLARO")
    else:
        print("ESCURO")
    time.sleep(0.1)
```

Passa o robô na mão em cima da linha e confirma que o print muda certo
na hora certa. Só depois disso faz sentido ligar motor.

### Passo 3 — Junta com o motor

```python
velocidade = 25

while True:
    leitura = robo.ler_sensor(porta=1, modo=p.MODO_COR_REFLETIDA)

    if leitura > limiar:
        # claro -> queremos voltar pra linha, então gira nessa direção
        robo.mover_continuo('B', velocidade)
        robo.mover_continuo('C', velocidade // 3)
    else:
        # escuro -> gira pro outro lado
        robo.mover_continuo('B', velocidade // 3)
        robo.mover_continuo('C', velocidade)

    time.sleep(0.05)
```

Se o robô girar pro lado errado (sair da linha em vez de voltar pra
ela), inverte qual bloco (`if`/`else`) faz qual motor acelerar.

### Passo 4 — Para direito

Sem isso, o motor fica ligado depois que você aperta Ctrl+C:

```python
try:
    while True:
        ...  # o loop do passo 3
except KeyboardInterrupt:
    robo.parar_motor('B')
    robo.parar_motor('C')
```

## 4. Função pronta da lib

Tudo isso (mais calibração automática) já tá em `jacarev3.topicos.circuito`:

```python
from jacarev3 import RoboEV3
from jacarev3.topicos import circuito

with RoboEV3('00:16:53:64:F8:B8') as robo:
    circuito.seguir_linha(robo, porta_sensor=1, verboso=True)
```

`verboso=True` imprime leitura + decisão a cada iteração — usa isso
enquanto ainda tá calibrando/entendendo, desliga quando já confia na
lógica (fica mais rápido sem o print).

## 5. Pra ir além

- Troca o bang-bang por um controle **proporcional**: quanto mais longe
  do limiar a leitura tá, mais forte a correção (em vez de sempre a
  mesma velocidade fixa)
- Faz o robô detectar quando perdeu a linha de vez (leitura não muda por
  muito tempo) e parar/apitar avisando
- Ajusta a velocidade de acordo com uma curva mais fechada vs. reta

Tem uma lista de exercícios em 4 níveis de dificuldade, desse módulo
e dos outros, em [Atividades](atividades.md#seguir-linha-circuito).
