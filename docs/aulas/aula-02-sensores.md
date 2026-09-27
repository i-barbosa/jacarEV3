# Aula 2 — Sensores

**Duração:** 50 minutos · **Turma:** já fez a [Aula 1](aula-01-primeiro-contato.md)

## Objetivo

No fim da aula, todo aluno sabe ler um sensor em loop e calibrar
manualmente um limiar — a base de qualquer robô que reage ao ambiente.

## Pré-requisitos

- [Aula 1](aula-01-primeiro-contato.md) — sabe rodar `RoboEV3`, com ou
  sem hardware
- Sensor de cor **e** ultrassônico disponíveis por grupo (com robô
  físico) ou `ConexaoFalsa` configurada (ver [sem-robo.md](../sem-robo.md))

## Material

- Fita preta e superfície clara (ou o contrário) pra testar o sensor de
  cor, se tiver robô físico
- Um objeto qualquer (livro, caixa) pra testar o ultrassônico

## Roteiro

**0–5 min — Recapitular + o problema de hoje**
Pergunta: "como o robô sabe que tem uma linha preta no chão?" — leva
pro conceito de sensor devolvendo número, não "sim/não" mágico.

**5–20 min — Leitura única, várias vezes**
Cada aluno/grupo roda:

```python
from jacarev3 import RoboEV3, protocolo as p

with RoboEV3('00:16:53:64:F8:B8') as robo:
    for _ in range(10):
        print(robo.ler_sensor(1, p.MODO_COR_REFLETIDA))
```

Move o sensor entre claro e escuro enquanto o loop roda, anota os
números que aparecem. Isso é literalmente o
[Nível 2 de básico](../atividades.md#basico-som-led-motor-sensor).

**20–35 min — Calibrar de verdade**
Introduz o conceito de **limiar**: a média entre o valor no claro e no
escuro. Cada grupo calcula o próprio (não usa um número genérico —
iluminação da sala muda o valor real):

```python
claro = float(input("Valor no claro: "))
escuro = float(input("Valor no escuro: "))
limiar = (claro + escuro) / 2
print(f"Seu limiar: {limiar}")
```

Ou já usa a versão pronta: `jacarev3.topicos.circuito.calibrar()` (só
mostra depois de todo mundo ter feito na mão pelo menos uma vez — o
objetivo é entender o cálculo, não só chamar a função).

**35–45 min — Mesma coisa com o ultrassônico**
Repete o padrão pro sensor de distância — sem "limiar" dessa vez, só
confirma a leitura em cm com o objeto em 3 distâncias diferentes.

**45–50 min — Fechamento**
Pergunta de saída: "o limiar de vocês vai funcionar na mesa do colega
do lado?" — normalmente não, e é esse o gancho pra próxima aula (por
que `seguir_linha()` calibra sozinha por padrão).

## Falhas comuns

| Sintoma | Causa provável | O que fazer |
|---|---|---|
| Leitura sempre igual, não muda | Sensor no modo errado (`MODO_COR_COR` em vez de `MODO_COR_REFLETIDA`) | Confere a constante usada |
| Ultrassônico lendo valor gigante/estranho | Nada na frente pra refletir o sinal | Normal, é o "infinito" do sensor |
| `ErroDePorta` | Confundiu porta de sensor (número) com motor (letra) | Ver a mensagem de erro — ela já diz qual é qual |

## Rubrica

- [ ] Leu sensor em loop e observou o valor mudar
- [ ] Calculou o próprio limiar (não copiou um número de exemplo)
- [ ] Sabe explicar por que o limiar de um grupo pode não servir pro outro
