# Changelog

Todas as mudanças notáveis desse projeto são documentadas aqui.
Formato baseado em [Keep a Changelog](https://keepachangelog.com/pt-BR/1.0.0/),
versionamento segue [SemVer](https://semver.org/lang/pt-BR/).

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
