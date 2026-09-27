# Competição (OBR, FLL e afins)

## 1. Conceito

Em competição, a régua é **repetibilidade**: o robô precisa fazer a
mesma coisa, na mesma pista, rodada após rodada — bateria descarregando
um pouco, atrito mudando com a temperatura, nada disso pode fazer o
robô parar 5cm mais longe da terceira vez que ele fez a mesma manobra.

`girar_motor(duracao_ms=...)` gira **por tempo**. Bateria fraca faz o
motor girar mais devagar no mesmo tempo — ou seja, menos distância. Não
é bug da lib, é física: tempo fixo não é distância fixa.

`girar_motor_graus`/`mover_base_graus` usam o **encoder** do motor — o
EV3 conta o eixo girando de verdade e para exatamente no grau pedido,
com bateria cheia ou quase acabando. Ver
[Precisão de motor](base-motriz.md) pro tutorial completo; essa página
assume que você já leu aquele.

## 2. Peças que você precisa

O mesmo de sempre — motores na base, robô montado. Nenhuma peça extra;
a diferença aqui é só qual método você chama.

## 3. Construindo passo a passo

### Passo 1 — Trocar tempo por grau em tudo que for distância

Se seu código hoje tem `girar_motor('B', duracao_ms=1500)` pra "andar
até tal ponto", o primeiro passo é **medir** quantos graus isso
corresponde de verdade, e trocar por `girar_motor_graus`:

```python
robo.zerar_graus_motor('B')
robo.girar_motor('B', velocidade=30, duracao_ms=1500)
print(robo.ler_graus_motor('B'))   # anota esse número
```

Depois disso, usa o número anotado direto:

```python
robo.girar_motor_graus('B', graus=<o número anotado>, velocidade=30)
```

Repete o mesmo teste 3 vezes com a bateria em níveis diferentes de
carga — o valor por tempo varia; o valor por grau, não.

### Passo 2 — Base sincronizada em vez de dois motores soltos

Duas chamadas de `girar_motor` (uma por roda) podem desalinhar um
pouco entre si — cada uma é um comando separado que o firmware não
sabe que devia estar junto. `mover_base_graus` sincroniza os dois
motores num comando só:

```python
robo.definir_base('B', 'C')  # se ainda não é o padrão do seu robô
robo.mover_base_graus(graus=720, velocidade=40, direcao=0)
```

`direcao=0` é reto. Pra virar num ângulo específico, mede empiricamente
quantos graus de `mover_base_graus` com `direcao=200` (giro no próprio
eixo) correspondem a quantos graus de giro do robô — isso depende do
diâmetro da roda e da distância entre elas, então é mais rápido medir
no seu robô que calcular.

### Passo 3 — Testar entre rodadas, não só uma vez

`motor_ocupado`/`esperar_motor` deixam o script esperar o movimento
terminar de verdade antes de continuar — importante quando a manobra
seguinte depende da anterior ter completado:

```python
robo.mover_base_graus(graus=360, velocidade=30, esperar=True)
# só chega aqui depois que os motores realmente pararam
robo.girar_motor_graus('D', graus=90, velocidade=50)  # ex: braço/garra
```

## 4. Função pronta da lib

Tudo isso já é API principal do `RoboEV3` — não tem tópico separado.
Tabela completa em [Precisão de motor](base-motriz.md#4-funcao-pronta-da-lib).

## 5. Pra ir além

!!! danger "Meça no seu robô, não confie só na teoria"
    Diâmetro de roda, atrito, peso — tudo isso muda a conversão
    graus↔distância de robô pra robô. O número certo pro seu robô só
    sai medindo nele, não copiando de outro time.

- Monta uma "planilha de calibração" do seu robô: quantos graus =
  1 volta completa da roda = quantos cm de deslocamento, medido de
  verdade com trena
- Testa o mesmo percurso de missão 5 vezes seguidas, mede o desvio
  entre elas — é essa variação que decide se o robô é "confiável" ou não
- Se o percurso muda de piso (tapete de competição vs. chão de casa),
  refaz a calibração — atrito muda o resultado

## Conexão

Bluetooth é a opção testada; em competição, considera também
[conectar por USB](usb.md) — menos gente pra parear no dia do evento,
mas **ainda não validado em hardware físico** (aviso na própria página).
Testa com antecedência, nunca no dia da competição.
