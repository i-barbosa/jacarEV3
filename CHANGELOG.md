# Changelog

Todas as mudanças notáveis desse projeto são documentadas aqui.
Formato baseado em [Keep a Changelog](https://keepachangelog.com/pt-BR/1.0.0/),
versionamento segue [SemVer](https://semver.org/lang/pt-BR/).

## [0.5.0] - 2026-09-27

### Adicionado
- `jacarev3.falso.ConexaoFalsa` — "robô de mentira": mesmo contrato de
  `ConexaoBluetooth`/`ConexaoUSB`, mas sem tocar em hardware. Sensor
  configurável por porta/modo (valor fixo ou função), `verboso=True`
  imprime cada comando reconhecido. Serve pra dar aula sem robô físico
  e pra teste automatizado. Ver [docs/sem-robo.md].
- `jacarev3.conexao.ConexaoUSB` — transporte USB via HID (`hidapi`,
  extra `jacarev3[usb]`). VID/PID e formato do relatório HID
  (report ID + 1024 bytes) confirmados contra duas implementações de
  referência independentes já testadas em hardware (BrianPeek/legoev3
  em C#, ChristophGaukel/ev3-python3 em Python) — **ainda não testado
  fisicamente nessa lib**. Ver [docs/usb.md].
- `jacarev3.transporte.Transporte` — `typing.Protocol` formalizando o
  contrato que `RoboEV3.conexao` já esperava implicitamente.
- **Type hints em 100% do código**, `py.typed` publicado no pacote —
  `mypy` roda limpo em `src/jacarev3` inteiro, e agora faz parte do CI.
- CI (`testes.yml`) ganha matriz de sistema operacional
  (`ubuntu-latest` + `windows-latest`) e um job de lint/type
  (`ruff check` + `mypy`), que também gateia o publish no PyPI.
- Docs novos: [Precisão de motor](docs/base-motriz.md) (encoder, motor
  por graus, base sincronizada — só existia em código, sem tutorial),
  [Conectar por USB](docs/usb.md), [Dar aula sem robô](docs/sem-robo.md),
  [Competição — OBR/FLL](docs/competicao.md), e 3 planos de aula de
  50 minutos em `docs/aulas/`.
- `CONTRIBUTING.md`, `CODE_OF_CONDUCT.md`, `SECURITY.md`, templates de
  issue (bug, funcionalidade, validação em hardware) e de PR,
  `.github/dependabot.yml`.

### Corrigido
- Dois lint nits pré-existentes (`RUF046`, import não ordenado).
- `topicos.controle`/`topicos.circuito`/`topicos.desvio` não tinham
  `robo` tipado como `RoboEV3` — nada mudou em runtime, só ficou
  checável estaticamente.

### Observado durante a tipagem
- `velocidade` sempre precisou ser `int` de verdade (a codificação usa
  `struct.pack('<b', ...)`, que não aceita `float`) — passar um valor
  fracionário sempre quebrou com `struct.error` cru, em qualquer versão
  anterior. Isso não mudou; agora é só declarado explicitamente
  (`velocidade: int`), então o `mypy` acusa antes de rodar, em vez de
  descobrir em tempo de execução.

## [0.4.2] - 2026-09-26

### Adicionado
- `jacarev3.erros` — hierarquia de exceções própria (`ErroJacare` na
  base). Cada uma continua herdando da exceção padrão mais parecida
  (`ValueError`, `KeyError`, `OSError`, `TimeoutError`), então código que
  já fazia `except ValueError:`/`except KeyError:` continua funcionando.
- Validação de velocidade (-100 a 100) em `girar_motor`, `mover_continuo`,
  `girar_motor_graus`, `mover_base` e `mover_base_graus` — antes,
  `velocidade=200` virava `struct.error` cru.
- `ConexaoBluetooth` agora traduz falha de conexão/timeout/queda no meio
  do envio em `ErroDeConexaoBluetooth`/`TempoEsgotado`, com mensagem que
  aponta o que conferir (pareamento, EV3 ligado). Antes era `OSError`
  cru sem contexto.
- 35 testes novos em `tests/test_erros.py`.

### Corrigido
- Porta de motor/sensor errada agora levanta `ErroDePorta` com mensagem
  que ensina — inclusive quando é o erro clássico de confundir letra
  (motor) com número (sensor). Antes: `KeyError: 'b'` cru, e
  `girar_motor('b')` minúsculo simplesmente não funcionava.
- `testar_motores()`/`testar_sensores()` não escondem mais uma queda de
  conexão como "[AVISO] Sem motor/sensor" — só erro do próprio EV3
  (porta vazia, tipo errado) é reportado por porta; queda de Bluetooth
  interrompe o scan inteiro.
- `_enviar()` levanta `ErroNoEV3` (era `RuntimeError` genérico) quando o
  EV3 responde tipo 0x04.
- `parse_resposta()` levanta `ErroDeProtocolo` (era `ValueError`
  genérico) pra resposta curta demais.

## [0.4.1] - 2026-09-26

### Adicionado
- `RoboEV3(portas=...)` — dict opcional mapeando porta pra apelido (e,
  pra sensor, tipo fixo), ex: `{'B': 'motor_esquerda', 1: ('cor', 'cor')}`.
  Quando definido, `testar_motores()`, `testar_sensores()` e
  `testar_tudo()` só varrem as portas listadas ali (com o apelido
  aparecendo no console), em vez de sempre varrer A-D e 1-4 inteiro.
  Sem `portas=`, o comportamento continua idêntico ao de antes. 5 testes
  novos em `tests/test_protocolo.py` cobrindo apelido, tipo fixado e o
  filtro de varredura.
- `jacarev3.topicos.controle` volta a aparecer em `jacarev3.topicos`
  (tinha ficado de fora do `__init__.py` do submódulo desde a 0.3.0).
- `publish.yml` roda a suíte de testes antes de publicar no PyPI — tag
  não sobe mais pacote com teste vermelho.

### Corrigido
- `topicos.__init__` reexportava só `circuito` e `desvio`; `controle`
  só funcionava por import direto (`from jacarev3.topicos import
  controle`), não pelo pacote (`jacarev3.topicos.controle`).

## [0.4.0] - 2026-09-18

### Adicionado
- `jacarev3.fontes` — de onde vêm os comandos do controle remoto.
  `FonteTeclado` (teclado do PC) e `FonteUDP` (controle físico pela rede,
  tipo um ESP32). Fonte nova é um objeto com `ler()` e suporte a `with`.
- `exemplos/esp32_controle.py` — firmware MicroPython de um controle de 4
  botões que manda o estado por UDP. Roda no MicroPython de fábrica.
- Testes do loop de controle e das fontes (`tests/test_controle.py`),
  incluindo o caso em que a fonte fica muda e o robô tem que parar.

### Mudado
- `controle_remoto()` agora recebe `fonte=` em vez de ter o teclado
  embutido. Sem fonte, continua usando o teclado — chamadas antigas
  seguem funcionando.
- Parâmetros `teclas`, `tecla_parar` e `tecla_sair` saíram do
  `controle_remoto()` e foram pra `FonteTeclado`, que é quem sabe o que
  é uma tecla.

## [0.3.0] - 2026-09-18

### Adicionado
- Movimento por graus e por voltas: `girar_motor_graus()` e
  `girar_motor_voltas()` (opOUTPUT_STEP_SPEED com rampa opcional). Era o
  buraco anotado em "Conhecido" desde a 0.1.0.
- Encoder: `ler_graus_motor()` (opOUTPUT_GET_COUNT) e `zerar_graus_motor()`
  (opOUTPUT_CLR_COUNT).
- Estado do motor: `motor_ocupado()` (opOUTPUT_TEST) e `esperar_motor()`,
  que espera perguntando ao brick em vez de usar opOUTPUT_READY — esse
  travaria a VM do EV3 e o socket durante o movimento inteiro.
- Base motriz sincronizada: `definir_base()`, `mover_base()`
  (opOUTPUT_TIME_SYNC), `mover_base_graus()` (opOUTPUT_STEP_SYNC) e
  `parar_base()`. Os dois motores andam travados um no outro, com turn
  ratio de -200 a 200.
- `jacarev3.teclado` — leitura de teclas sem bloquear, Windows e Unix.
- `jacarev3.topicos.controle` — controle remoto pelo teclado do PC, com
  parada automática no brick se o computador parar de responder.
- `RoboEV3(conexao=...)` aceita um transporte pronto, o que permite testar
  a biblioteca inteira sem robô ligado (e abre caminho pra WiFi/USB).
- Opcodes de motor que faltavam em `protocolo.py`: RESET, POWER, SPEED,
  START, POLARITY, READ, TEST, READY, STEP_POWER, TIME_POWER, STEP_SYNC,
  TIME_SYNC, CLR_COUNT, GET_COUNT.
- Suíte de testes de encoding (`tests/`), 29 casos, roda sem hardware.

### Corrigido
- `mover_continuo()` usava opOUTPUT_STEP_SPEED com um step2 de 2 bilhões
  pra simular movimento infinito. Agora usa opOUTPUT_SPEED seguido de
  opOUTPUT_START, que é o jeito documentado no firmware.
- `ler_graus_motor()` passa o índice da porta (0-3), não o bitmask: o
  firmware indexa `pMotor[No]` direto em `cOutputGetCount`, apesar da
  documentação chamar o parâmetro de "bit field". Quem passasse 0x04 pra
  ler o motor C leria a porta errada.

### Conhecido
- Testado offline (encoding); a validação no robô físico continua pendente.
- Sem suporte a WiFi/USB ainda (só Bluetooth clássico).

## [0.2.1] - 2026-09-17

### Corrigido
- Logo do README agora usa URL absoluta — a página do PyPI não resolve
  caminho relativo, então o logo aparecia quebrado lá. Links pro LICENSE e
  pro CHANGELOG também viraram absolutos pelo mesmo motivo.
- `__version__` estava travado em "0.1.0" enquanto o pacote já era 0.2.0.
  Agora o `pyproject.toml` lê a versão de `jacarev3.__init__` (setuptools
  dynamic), então existe um lugar só pra mudar.

### Adicionado
- README documenta o que entrou na 0.2.0: `ler_sensor()`, `mover_continuo()`
  e o submódulo `jacarev3.topicos`, com link pros tutoriais em `docs/`.
- `jacarev3` re-exporta `protocolo` e `topicos`; `jacarev3.topicos`
  re-exporta `circuito` e `desvio`. Antes `from jacarev3 import protocolo`
  só funcionava por acidente do import machinery.
- Extra de desenvolvimento: `pip install -e ".[dev]"` (pytest, ruff, mypy).
- `MANIFEST.in` põe `docs/`, `assets/` e o CHANGELOG no sdist.
- `.editorconfig`.

## [0.2.0] - 2026-09-17

### Adicionado
- Submódulo `jacarev3.topicos` — receitas prontas de robótica educacional:
  - `topicos.circuito.seguir_linha()` — seguir linha preta (bang-bang) +
    `calibrar()` automática
  - `topicos.desvio.desviar_obstaculo()` — desviar de obstáculo com
    sensor ultrassônico
- `RoboEV3.ler_sensor()` — leitura direta de sensor (pra loops de controle)
- `RoboEV3.mover_continuo()` — motor contínuo sem parar sozinho

## [0.1.0] - 2026-09-17

### Adicionado
- Protocolo "Direct Commands" do EV3 implementado do zero (`protocolo.py`),
  sem dependência de bibliotecas de terceiros — só stdlib do Python.
- Conexão Bluetooth clássica (RFCOMM) via `socket.AF_BLUETOOTH` (`conexao.py`).
- API em português (`RoboEV3`):
  - `apitar()`, `led()`
  - `girar_motor()`, `parar_motor()`, `testar_motor()`, `testar_motores()`
  - `testar_ultrassonico()`, `testar_toque()`, `testar_cor()`,
    `testar_sensores()`, `testar_tudo()`
- Encoding de pacotes validado byte a byte contra os exemplos oficiais do
  "LEGO MINDSTORMS EV3 Communication Developer Kit" (som, sensor, motor).

### Conhecido
- Testado offline (encoding); ainda em validação no robô físico.
- Sem suporte a WiFi/USB ainda (só Bluetooth clássico).
- Movimento de motor é por tempo, não por graus/posição.
