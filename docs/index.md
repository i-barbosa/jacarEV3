# jacarEV3 🐊

Lib em português pra controlar o LEGO EV3 via Bluetooth. Protocolo
"Direct Commands" implementado do zero a partir da documentação pública
da LEGO — nenhuma dependência externa, só biblioteca padrão do Python.

```python
from jacarev3 import RoboEV3

with RoboEV3('00:16:53:64:F8:B8') as robo:  # MAC do seu EV3
    robo.apitar()
    robo.led('VERDE')
    robo.testar_tudo()  # testa motores A-D e sensores 1-4
```

```bash
pip install jacarev3
```

## Por que essa lib existe

A maioria das libs pra EV3 em Python depende do
[`ev3_dc`](https://github.com/ChrStBaer/ev3-dc) (GPLv3), tem API em
inglês, ou assume conhecimento prévio de protocolo binário. `jacarEV3`
resolve os três problemas: protocolo próprio (clean-room, a partir do
*Communication Developer Kit* da LEGO), zero dependências, e toda a
API — nomes de método, parâmetros, mensagens de erro — em português.

<div class="grid cards" markdown>

-   :material-connection:{ .lg .middle } **Bluetooth clássico**

    ---

    Conexão RFCOMM via `socket.AF_BLUETOOTH` da stdlib. Sem pareamento
    frágil de driver, sem biblioteca de terceiros pra instalar.

-   :material-flask-outline:{ .lg .middle } **Testável sem robô**

    ---

    `RoboEV3(conexao=...)` aceita qualquer transporte que implemente
    `enviar`/`receber` — dá pra simular o EV3 inteiro num teste, sem
    hardware ligado.

-   :material-translate:{ .lg .middle } **API em português**

    ---

    `girar_motor`, `ler_sensor`, `testar_tudo` — pensada pra quem tá
    aprendendo robótica em português, não traduzindo mentalmente do
    inglês antes.

-   :material-school-outline:{ .lg .middle } **Feita pra ensinar**

    ---

    Cada tópico vem com um tutorial que explica a lógica por trás, não
    só a função pronta. A ideia é entender como construir.

</div>

## Tutoriais por tópico

<div class="grid cards" markdown>

-   :material-numeric-1-circle-outline: **[Básico](basico.md)**

    ---

    Som, LED, motor por tempo e leitura de sensor — os fundamentos
    antes de qualquer robô autônomo.

-   :material-numeric-2-circle-outline: **[Seguir linha](circuito.md)**

    ---

    Sensor de cor + controle bang-bang pra seguir uma linha preta no
    chão. O clássico da robótica educacional.

-   :material-numeric-3-circle-outline: **[Desviar de obstáculo](desvio.md)**

    ---

    Sensor ultrassônico pra parar, girar e desviar de algo no caminho.

-   :material-numeric-4-circle-outline: **[Controle remoto](controle.md)**

    ---

    Dirigir a base motriz pelo teclado do PC ou por um controle físico
    de ESP32 na rede, com parada automática por segurança.

</div>

## Padrão dos tutoriais

Todo tutorial em `docs/` segue a mesma estrutura, pra manter a lib
consistente pra quem tá estudando:

1. **Conceito** — o que é a tarefa, por que é clássica em robótica
2. **Peças que você precisa** — sensor(es)/motor(es) e como montar
3. **Construindo passo a passo** — código crescendo em pedaços pequenos,
   cada um rodável e testável sozinho antes de juntar tudo
4. **Função pronta da lib** — a versão final, já otimizada, disponível
   em `jacarev3.topicos`
5. **Pra ir além** — variações pra tentar sozinho (é aqui que a
   aprendizagem de verdade acontece)

!!! tip "Escrevendo um tópico novo"
    Se for contribuir com um tutorial, usa esse mesmo formato de 5
    seções. Issues e PRs são bem-vindos em
    [github.com/i-barbosa/jacarEV3](https://github.com/i-barbosa/jacarEV3).

## Status

A versão publicada, changelog completo e a licença MIT ficam no
[repositório no GitHub](https://github.com/i-barbosa/jacarEV3) e na
[página do PyPI](https://pypi.org/project/jacarev3/).
