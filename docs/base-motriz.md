# Precisão de motor — graus, encoder e base sincronizada

## 1. Conceito

`girar_motor(porta, duracao_ms=...)` gira **por tempo** — bom pra
protótipo rápido, ruim pra precisão: 500ms de motor não é sempre a
mesma distância (bateria fraca, atrito, chão diferente mudam quanto o
robô anda naquele meio segundo).

O EV3 tem um **encoder** em cada motor — um sensor que conta quantos
graus o eixo girou, de verdade, com o motor girando ou não. Pedir "gira
360 graus" é uma ordem que o firmware do próprio EV3 cumpre sozinho,
sem depender de `time.sleep` do lado do Python.

A base motriz (os dois motores da roda) também tem um comando
**sincronizado** — os dois motores recebem uma única ordem e o
firmware trava a velocidade de um no outro, em vez de você mandar dois
`girar_motor()` separados que podem desalinhar.

## 2. Peças que você precisa

- 2 motores formando a base motriz (o mesmo `'B'`/`'C'` de sempre)
- Espaço livre — os exercícios de grau pedem o robô andando reto de
  verdade, não só girando uma roda no ar

## 3. Construindo passo a passo

### Passo 1 — Ler o encoder parado

Antes de girar qualquer coisa, confirma que o encoder existe e o que
ele devolve:

```python
from jacarev3 import RoboEV3

with RoboEV3('00:16:53:64:F8:B8') as robo:
    print(robo.ler_graus_motor('B'))
```

Gira o motor **na mão** (com o robô desligado do controle, só
empurrando a roda) e roda o `ler_graus_motor` de novo — o número muda
mesmo sem nenhum comando de movimento ter sido mandado. O encoder conta
sempre, é passivo.

### Passo 2 — Zerar a referência

O número que o encoder mostra é **desde o último zeramento**, não
"ângulo absoluto do motor". Sem zerar, o primeiro `ler_graus_motor` já
pode vir com lixo de testes anteriores:

```python
robo.zerar_graus_motor('B')
print(robo.ler_graus_motor('B'))  # 0
```

### Passo 3 — Girar uma quantidade exata de graus

```python
robo.girar_motor_graus('B', graus=360, velocidade=30)
print(robo.ler_graus_motor('B'))  # ~360
```

`graus` é sempre positivo — quem decide o sentido é o sinal de
`velocidade`. Isso é diferente de `girar_motor()`, onde `duracao_ms`
também é sempre positivo mas por outro motivo (é tempo, não teria
sentido negativo).

Por padrão a função **bloqueia** (`esperar=True`) até o motor terminar
— ela pergunta ao EV3 de tempos em tempos se ainda tá girando
(`motor_ocupado()`), em vez de usar um `time.sleep` chutado. Se quiser
disparar e seguir fazendo outra coisa:

```python
robo.girar_motor_graus('B', graus=360, velocidade=30, esperar=False)
# ... faz outra coisa aqui ...
robo.esperar_motor('B')  # bloqueia só agora, se ainda tiver girando
```

### Passo 4 — Mover a base sincronizada

Pra andar reto de verdade (os dois motores não perdem sincronia um do
outro), usa `mover_base` em vez de dois `girar_motor` separados:

```python
robo.mover_base(velocidade=30, direcao=0, duracao_ms=1000)
```

`direcao` vai de -200 a 200: `0` é reto, `-100`/`+100` trava um motor
(curva fechada), `±200` gira no próprio eixo. É o "turn ratio" do
firmware — o mesmo conceito do volante de um carro, só que em vez de
graus é uma escala de -200 a 200.

Repara que `mover_base` **não bloqueia** e tem `duracao_ms`: se você
parar de chamar ela, o EV3 desliga os motores sozinho quando o tempo
acaba. É a mesma lógica de segurança do [controle remoto](controle.md)
— nenhuma função de movimento contínuo aqui depende de uma mensagem de
"parar" que pode nunca chegar.

### Passo 5 — Andar uma distância exata

```python
robo.mover_base_graus(graus=720, velocidade=30, direcao=0)
```

Isso sim bloqueia por padrão (`esperar=True`) — ao contrário de
`mover_base`, aqui você já sabe de antemão quanto tempo o movimento vai
durar (até completar os graus pedidos), então esperar faz sentido.

## 4. Função pronta da lib

Não tem um "tópico" separado pra isso (como `circuito`/`desvio`) — as
funções já são a API principal do `RoboEV3`:

| Método | Faz |
|---|---|
| `girar_motor_graus(porta, graus, velocidade=30, frear=True, esperar=True, rampa_graus=0)` | Um motor, quantidade exata de graus |
| `girar_motor_voltas(porta, voltas, **kwargs)` | Igual, mas em voltas (`voltas=2` = `graus=720`) |
| `ler_graus_motor(porta)` / `zerar_graus_motor(porta)` | Encoder |
| `motor_ocupado(porta)` / `esperar_motor(porta, tempo_limite=30)` | Estado do motor |
| `mover_base(velocidade=30, direcao=0, duracao_ms=500, frear=False)` | Base sincronizada, por tempo |
| `mover_base_graus(graus, velocidade=30, direcao=0, frear=True, esperar=True)` | Base sincronizada, por distância |
| `parar_base(frear=True)` / `definir_base(esquerda='B', direita='C')` | Parar os dois de vez / trocar quais motores formam a base |

## 5. Pra ir além

- Faz o robô andar um quadrado: `mover_base_graus` reto, depois
  `direcao=200` até girar 90° (mede quanto de `graus` isso precisa —
  não é o mesmo valor do avanço reto), repete 4 vezes
- Compara a precisão de `girar_motor(duracao_ms=...)` vs
  `girar_motor_graus(graus=...)`: manda os dois andarem "a mesma
  distância" várias vezes e mede a variação entre as tentativas
- Usa `ler_graus_motor` durante o [seguir linha](circuito.md) pra medir
  quantos graus o robô girou desde que a linha foi perdida — dá pra
  estimar o quanto ele desviou, sem sensor nenhum além do que já tem
