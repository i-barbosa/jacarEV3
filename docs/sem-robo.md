# Dar aula sem robô físico

## 1. Conceito

Numa sala com 30 alunos e 6 robôs, a maioria fica esperando a vez. Com
`jacarev3.falso.ConexaoFalsa`, todo mundo com computador roda o código
imediatamente — vê o print de "o que aconteceria", entende a lógica, e
só usa o robô de verdade quando chegar a vez (ou nem precisa, pra boa
parte da aula).

**Não é um simulador.** `ConexaoFalsa` não simula física, não sabe
"onde" o robô tá, não calcula trajetória. Ela só nunca trava esperando
um EV3 que não existe, e devolve um número plausível quando você pede
leitura de sensor. É uma dublê pra código rodar, não uma física de
jogo.

## 2. Peças que você precisa

Nenhuma. É esse o ponto.

## 3. Construindo passo a passo

### Passo 1 — Trocar a conexão, não o resto do código

```python
from jacarev3 import RoboEV3
from jacarev3.falso import ConexaoFalsa

with RoboEV3(conexao=ConexaoFalsa()) as robo:
    robo.apitar()
    robo.led('VERDE')
    robo.testar_tudo()
```

Roda exatamente como se fosse `RoboEV3('00:16:...')` — só que sem MAC,
sem parear, sem esperar. Todo `print` de `testar_tudo()`/`verboso=True`
continua aparecendo — é assim que a aula sem robô ainda parece que algo
tá acontecendo.

### Passo 2 — Configurar o que o sensor "vê"

Por padrão, todo sensor lê `50.0`, sempre. Pra ensinar uma lógica
específica (tipo bang-bang de [seguir linha](circuito.md)), configura o
valor por porta e modo:

```python
from jacarev3 import protocolo as p

conexao = ConexaoFalsa(valores_sensor={
    (0, p.MODO_COR_REFLETIDA): 20.0,   # porta física 1 (índice 0), "escuro"
})
```

A chave é `(índice_da_porta, modo)` — índice é a porta física menos 1
(porta 1 = índice 0), o mesmo número que vai no bytecode enviado pro
"EV3".

### Passo 3 — Sensor que muda ao longo do tempo

Pra testar uma lógica que reage a mudança (tipo
[desviar de obstáculo](desvio.md)), passa uma função em vez de um
número fixo — ela é chamada de novo a cada leitura:

```python
distancias = iter([80, 80, 80, 10, 10, 80, 80])  # "aproxima e afasta"

conexao = ConexaoFalsa(valores_sensor={
    (3, p.MODO_ULTRASSONICO_CM): lambda porta, modo: next(distancias, 80),
})

with RoboEV3(conexao=conexao) as robo:
    for _ in range(7):
        print(robo.ler_sensor(4, p.MODO_ULTRASSONICO_CM))
```

### Passo 4 — Testar sua própria lógica, sem `print`

Pra teste automatizado (não aula), `conexao.enviados` guarda todo
pacote que "saiu", na ordem — dá pra afirmar que o robô mandou o
comando certo, sem precisar rodar contra hardware nem ler print:

```python
conexao = ConexaoFalsa(verboso=False)
with RoboEV3(conexao=conexao) as robo:
    robo.led('VERDE')

assert len(conexao.enviados) == 1
```

## 4. Função pronta da lib

`jacarev3.falso.ConexaoFalsa(valores_sensor=None, valor_padrao=50.0, verboso=True)`
já é a peça pronta — não tem "tópico" separado, é só trocar o que entra
em `conexao=`.

## 5. Pra ir além

- Roda `circuito.seguir_linha()` inteiro contra uma `ConexaoFalsa` com
  `valores_sensor` alternando entre "claro" e "escuro" a cada chamada —
  dá pra ver a decisão (`CLARO -> girando pra direita` etc.) sem
  nenhum robô ligado
- Usa isso como primeira aula do semestre: todo aluno escreve e roda o
  próprio código no dia 1, antes de sequer ter acesso a um EV3 físico
- Se sua lógica precisa de encoder (`ler_graus_motor`), `ConexaoFalsa`
  sempre devolve 0 — não dá pra testar lógica que depende do encoder
  mudando, só que ela não quebra rodando
