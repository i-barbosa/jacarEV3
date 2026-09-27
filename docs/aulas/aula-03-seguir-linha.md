# Aula 3 — Seguir linha

**Duração:** 50 minutos · **Turma:** já fez a [Aula 2](aula-02-sensores.md)

## Objetivo

No fim da aula, todo grupo tem um robô seguindo uma linha preta —
usando a lógica bang-bang, construída em pedaços, não copiada pronta.

## Pré-requisitos

- [Aula 2](aula-02-sensores.md) — sabe ler sensor e calcular limiar
- Robô físico com sensor de cor montado apontando pro chão, 2 motores
  na base (esquerda/direita)

## Material

- Uma pista com linha preta em fundo claro por grupo (fita isolante
  preta numa cartolina branca resolve)

## Roteiro

**0–5 min — O conceito, sem código**
Desenha no quadro: sensor vê "claro" → robô devia virar pra um lado;
sensor vê "escuro" → vira pro outro. Isso é bang-bang: só duas decisões,
sem meio-termo.

**5–15 min — Decisão sem motor ainda**
Segue [circuito.md, passo 2](../circuito.md#passo-2-decisao-simples-sem-motor-ainda) —
só `print`, sem ligar motor nenhum. Passa o robô na mão em cima da
linha, confirma que o print muda na hora certa.

!!! tip "Não pula essa etapa"
    É tentador ir direto pro robô andando. Mas debugar "por que ele não
    segue a linha" é muito mais difícil quando motor e sensor mudam ao
    mesmo tempo. Confirma a decisão primeiro.

**15–35 min — Liga o motor**
Junta com motor, [passo 3 do tutorial](../circuito.md#passo-3-junta-com-o-motor).
Cada grupo ajusta `velocidade` e qual lado gira mais rápido pro próprio
robô (a lib documenta "se girar errado, inverte o `if`/`else`" — deixa
os grupos descobrirem isso testando, não avisa antes).

**35–45 min — Roda na pista de verdade**
Testa na pista, ajusta o limiar calculado na Aula 2 se não estiver bom
o suficiente. Introduz `circuito.seguir_linha()` como a versão pronta,
com calibração automática — só depois de já ter rodado a versão manual.

**45–50 min — Corrida (opcional) + fechamento**
Se der tempo, corrida entre grupos na mesma pista. Fechamento: qual
grupo teve o robô mais estável, e por quê (velocidade mais baixa? limiar
mais preciso?).

## Falhas comuns

| Sintoma | Causa provável | O que fazer |
|---|---|---|
| Robô sai da linha em vez de voltar | Lado invertido no `if`/`else` | Troca qual bloco aciona qual motor |
| Robô trava/oscila muito rápido | `velocidade` alta demais pro sensor reagir a tempo | Reduz `velocidade`, ou aumenta o `time.sleep()` do loop |
| Motor não para com Ctrl+C | Faltou o `try`/`finally` do [passo 4](../circuito.md#passo-4-para-direito) | Adiciona o `finally` com `parar_motor()` nos dois motores |

## Rubrica

- [ ] Robô segue a linha por pelo menos uma volta completa da pista
- [ ] Grupo sabe explicar por que inverteu (ou não precisou inverter) o `if`/`else`
- [ ] Ctrl+C para o robô de verdade (motor não fica girando sozinho)

## Pra continuar

[Nível 3 e 4 de circuito em Atividades](../atividades.md#seguir-linha-circuito) —
detector de linha perdida, e controle proporcional.
