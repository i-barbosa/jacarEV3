# Atividades por módulo

Um jeito de praticar cada tutorial em 4 níveis — do "só roda e vê o que
acontece" até um projeto aberto. Não tem gabarito publicado de
propósito: o objetivo é você (ou seu aluno) chegar lá mexendo,
comparando com quem tá do lado, discutindo por que uma solução funcionou
melhor que outra.

Cada nível pressupõe que você já leu o tutorial do módulo. Se ainda não
leu, começa por ele — as atividades usam a API que ele explica.

!!! tip "Travou?"
    Tem [respostas](gabaritos.md) — pelo menos 2 jeitos diferentes de
    resolver cada atividade. Mas tenta sozinho primeiro; comparar sua
    solução com outra depois de já ter pensado ensina mais do que ler a
    resposta de cara.

<div class="grid cards" markdown>

-   :material-numeric-1-circle-outline: **Nível 1 — Roda e observa**

    ---

    Chama a função pronta com parâmetros diferentes. Nenhuma linha de
    código nova — só entender o que cada parâmetro muda.

-   :material-numeric-2-circle-outline: **Nível 2 — Mede e calibra**

    ---

    Cria uma tabela/registro do que o sensor devolve no seu robô
    específico. Sem isso, os níveis seguintes viram chute.

-   :material-numeric-3-circle-outline: **Nível 3 — Muda a lógica**

    ---

    Escreve seu próprio loop (não a função de `jacarev3.topicos`) pra
    fazer o robô reagir diferente do padrão.

-   :material-numeric-4-circle-outline: **Nível 4 — Projeto aberto**

    ---

    Combina dois módulos, ou resolve um problema que a lib não
    resolveu pronto. É onde a maioria das ideias de verdade aparece.

</div>

## Básico — som, LED, motor, sensor

Tutorial: [básico.md](basico.md).

**Nível 1.** Chama `robo.apitar()` variando `frequencia` (ex: 220, 440,
880, 1760) e `volume` (1, 25, 100). Anota qual combinação seu alto-falante
realmente deixa mais alta — o parâmetro nem sempre corresponde ao que
você ouve.

**Nível 2.** Encosta o sensor ultrassônico em 5 distâncias diferentes
(5cm, 10cm, 20cm, 40cm, 80cm — mede com régua) e registra o que
`robo.ler_sensor(porta, p.MODO_ULTRASSONICO_CM)` devolve em cada uma.
Faz o mesmo pro sensor de cor: chão claro, chão escuro, uma folha de
papel colorida.

**Nível 3.** Escreve um loop que lê o sensor de toque a cada 0.1s e
conta quantas vezes ele foi apertado (não "está apertado", **quantas
vezes** — cuidado pra não contar o mesmo aperto várias vezes seguidas).

**Nível 4.** "Termômetro de proximidade": quanto mais perto um objeto
chega do ultrassônico, mais agudo o bipe (`apitar(frequencia=...)`) e
mais vermelho o LED (intercala `led('VERMELHO')`/`led('VERDE')`
proporcional à distância). Sem `time.sleep` fixo — a resposta tem que
ficar mais rápida quanto mais perto o objeto estiver.

??? tip "Dica pro nível 4"
    `frequencia` e o intervalo entre leituras podem ser os dois uma
    função da distância lida — não precisa de nada além de aritmética
    simples (tipo `1000 / distancia`).

## Seguir linha (`circuito`)

Tutorial: [circuito.md](circuito.md).

**Nível 1.** Roda `circuito.seguir_linha(robo, porta_sensor=1,
velocidade=25, duracao_s=15)` com `velocidade` em 15, 25, 40. Em qual o
robô perde a linha nas curvas? Em qual ele anda visivelmente devagar
demais?

**Nível 2.** Roda `circuito.calibrar(robo, porta_sensor=1)` no seu
tapete específico e usa o `limiar` que ele devolve, explícito, em vez de
deixar `seguir_linha` adivinhar. Compara a suavidade do seguimento antes
e depois.

**Nível 3.** Copia o loop bang-bang do tutorial (passo 3) e adiciona:
se a leitura não mudar por mais de 2 segundos, para os motores e apita
3 vezes ("perdi a linha"), em vez de continuar girando pro mesmo lado
pra sempre.

**Nível 4.** Troca o bang-bang por controle **proporcional**: em vez de
`velocidade` fixa pra cada lado, calcula o quanto a leitura atual está
longe do `limiar` e usa isso pra escalar a diferença de velocidade entre
as rodas continuamente (sem `if`/`else`, uma fórmula só). Mede o tempo
de volta na pista e compara com o bang-bang do nível 1.

??? tip "Dica pro nível 4"
    `erro = leitura - limiar`. Motor de um lado fica em
    `velocidade_base + erro * ganho`, do outro
    `velocidade_base - erro * ganho`. Comece com um `ganho` pequeno e
    vai aumentando até o robô oscilar — aí volta um pouco.

## Desviar de obstáculo (`desvio`)

Tutorial: [desvio.md](desvio.md).

**Nível 1.** Roda `desvio.desviar_obstaculo(robo, porta_sensor=4,
distancia_minima_cm=15)` variando `distancia_minima_cm` (5, 15, 30).
Com qual valor o robô bate antes de reagir? Com qual ele desvia de
coisas que nem estavam no caminho?

**Nível 2.** Anda com um objeto na mão se aproximando devagar do
sensor, imprimindo a leitura a cada 0.2s (igual ao nível 2 do básico,
mas documentando especificamente o seu sensor ultrassônico montado no
robô — a posição de montagem muda a leitura).

**Nível 3.** Adiciona uma contagem: quantos obstáculos o robô desviou
numa volta completa da pista, impressa no final (não durante — só o
total).

**Nível 4.** Combina com seguir linha: o robô segue a linha
normalmente, mas se o ultrassônico detectar algo mais perto que um
limite, para de seguir a linha, desvia, e **volta a procurar a linha**
depois (não simplesmente continua reto). É o primeiro módulo que pede
os dois sensores rodando no mesmo loop.

??? tip "Dica pro nível 4"
    Depois de desviar, gira devagar num sentido só, lendo o sensor de
    cor a cada leitura, até ele voltar a ver "escuro" — é assim que o
    robô "acha" a linha de novo sem saber onde ela ficou.

## Controle remoto (`controle`)

Tutorial: [controle.md](controle.md).

**Nível 1.** Roda `controle.controle_remoto(robo, verboso=True)` com o
teclado (sem precisar de controle físico) e depois com `FontePygame()`
se tiver um Xbox. Ajusta `velocidade=` e `giro=` até o robô responder do
jeito que você gosta.

**Nível 2.** Muda `zona_morta_giro` e `taxa_suavizacao` do
`FontePygame` pros extremos (`zona_morta_giro=0`, depois `=0.3`;
`taxa_suavizacao=1`, depois `=0.05`) e descreve em uma frase cada, o
que mudou na sensação de dirigir.

**Nível 3.** Faz um botão do controle (que ainda não faz nada) acionar
o LED verde ou apitar — sem mexer em `controle_remoto()`: lê o botão
direto no `joystick` dentro do seu próprio script, fora do loop da lib.

**Nível 4.** Escreve sua própria `Fonte` (a lib já ensina o contrato:
`ler()` + `with`) pra um jeito diferente de comandar o robô — outro
controle, um segundo eixo controlando um motor de garra, ou até um
`FonteMouse` que lê a posição do mouse na tela. Não existe resposta
certa aqui, só o contrato pra respeitar.

??? tip "Dica pro nível 4"
    Reveja o passo 4 do tutorial de controle — o exemplo `FonteMinhaIdeia`
    já é o esqueleto inteiro que falta preencher.
