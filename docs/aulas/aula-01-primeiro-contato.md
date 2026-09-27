# Aula 1 — Primeiro contato

**Duração:** 50 minutos · **Turma:** iniciante, primeiro dia com o EV3

## Objetivo

No fim da aula, todo aluno instalou a lib e rodou pelo menos 3 comandos
diferentes (som, LED, teste completo) — com robô físico ou sem.

## Pré-requisitos

- Python instalado (`python --version` funciona no terminal)
- `pip install jacarev3` já rodado antes da aula (pede pra fazer em
  casa — internet de sala costuma ser o gargalo real do dia)
- Se tiver robô físico disponível: já carregado, Bluetooth ligado

## Material

- 1 computador por aluno (ou dupla)
- 1 EV3 físico a cada 4-6 alunos, se tiver (não é obrigatório pra essa aula)

## Roteiro

**0–5 min — Abertura**
O que é o EV3, o que é essa lib, por que Python (não bloco). Mostra o
[site da lib](../index.md) na tela, sem entrar em código ainda.

**5–15 min — Primeiro comando, sem robô nenhum**
Todo mundo roda, independente de ter robô físico:

```python
from jacarev3 import RoboEV3
from jacarev3.falso import ConexaoFalsa

with RoboEV3(conexao=ConexaoFalsa()) as robo:
    robo.apitar()
    robo.led('VERDE')
```

Pergunta: "o que vocês acham que aconteceu?" — ninguém ouviu bipe
nenhum, e tá certo, é o robô de mentira ([sem-robo.md](../sem-robo.md)).
O ponto aqui é confirmar que o Python roda, sem depender de hardware.

**15–30 min — Quem tem robô físico, conecta de verdade**
Grupos com EV3 disponível trocam `ConexaoFalsa()` pelo MAC do robô
(`RoboEV3('00:16:53:64:F8:B8')` — o MAC tá nas configurações Bluetooth
do EV3, em Settings → Bluetooth). Grupos sem robô continuam com
`ConexaoFalsa`, mexendo nos parâmetros de `apitar`/`led`. Se der
`OSError`/timeout: confere se o EV3 tá pareado no sistema (não só
ligado) — ver a tabela de falhas comuns no fim dessa página.

**30–45 min — Exercício guiado**
Todo mundo (com robô ou sem) faz o Nível 1 de
[Atividades > Básico](../atividades.md#basico-som-led-motor-sensor):
variar `frequencia`/`volume` do `apitar()`.

**45–50 min — Fechamento**
Quem conseguiu conectar de verdade, roda `robo.testar_tudo()` uma vez
pra turma ver o robô reagir. Anuncia o tema da próxima aula (sensores).

## Falhas comuns

| Sintoma | Causa provável | O que fazer |
|---|---|---|
| `OSError`/timeout ao conectar | EV3 não pareado, ou desligado | Confere Bluetooth do EV3 ligado, repareia no sistema |
| `pip install jacarev3` falha | Sem internet, ou `pip` não é do Python certo | Testa `python -m pip install jacarev3` |
| Nada acontece com `ConexaoFalsa` | Normal — é o esperado, sem som/LED de verdade | Confirma que não deu exceção, é sucesso |

## Rubrica

- [ ] Rodou `apitar()`/`led()` sem erro (com ou sem robô)
- [ ] Alterou pelo menos um parâmetro (frequência, volume, cor) e viu o efeito
- [ ] Sabe explicar, em uma frase, a diferença entre `RoboEV3(mac)` e `RoboEV3(conexao=ConexaoFalsa())`
