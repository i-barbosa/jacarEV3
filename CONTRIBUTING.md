# Contribuindo com o jacarEV3

Issues e PRs são bem-vindos. Esse guia existe pra você não perder tempo
com um PR que vai esbarrar numa regra do projeto — lê antes de codar.

## As duas regras que não têm exceção

### 1. A API é só em português

`girar_motor`, não `spin_motor`. `ler_sensor`, não `read_sensor`. Sem
alias em inglês, sem README bilíngue. É o diferencial do projeto —
existir uma lib de robótica educacional pensada em português do zero,
não traduzida por cima de uma em inglês.

Isso vale pra nomes de método, parâmetro, classe e mensagem de erro.
Comentário de código pode citar termo técnico em inglês quando não tem
tradução natural (`"turn ratio"`, `"report ID"`), mas a API pública não.

### 2. Opcode novo só de fonte pública e citada

Todo opcode em `protocolo.py` vem de duas fontes oficiais da LEGO: o
*Communication Developer Kit* (PDF público) e `bytecodes.h` (header do
firmware, publicado em github.com/mindboards/ev3sources). Isso é o que
mantém o projeto livre de contaminação por código GPLv3 (tipo o
`ev3_dc`) — ver o cabeçalho de `protocolo.py` pra entender por quê.

Se for adicionar opcode novo:
- Cita a fonte (nome do documento + página, ou nome da constante em
  `bytecodes.h`) num comentário perto da constante
- **Não copia de outra lib** (nem trecho pequeno) nem de transcrição de
  chat/IA — sempre da fonte primária
- Se envolve leitura de resposta do EV3, escreve o teste de encoding
  junto (ver abaixo)

Uma issue perguntando "de onde veio esse valor?" numa PR que adiciona
opcode é normal, não desconfiança.

## Rodando o projeto localmente

```bash
git clone https://github.com/i-barbosa/jacarEV3.git
cd jacarEV3
pip install -e ".[dev]"
pytest -q
ruff check src/ tests/
mypy src/jacarev3
```

Os três (`pytest`, `ruff`, `mypy`) rodam no CI (`.github/workflows/testes.yml`)
em toda PR — roda local antes de abrir, economiza uma volta.

**Nenhum teste precisa de EV3 físico.** `RoboEV3(conexao=...)` aceita
qualquer objeto com `proximo_contador()`/`enviar()`/`receber()`/`fechar()`
— é assim que a suíte inteira (100+ testes) roda sem hardware. Veja
`tests/test_protocolo.py` (`ConexaoFalsa`) pro padrão usado.

## O que testar de verdade, com robô

O projeto tem uma lacuna conhecida: **nada aqui foi validado num EV3
físico ainda** (Bluetooth é o mais próximo de testado; USB não foi
testado nenhuma vez). Se você tem um EV3 em mãos, testar qualquer parte
da lib contra hardware real e reportar o resultado (funcionou ou não)
é uma das contribuições mais valiosas possíveis agora — mais que
feature nova.

## Estilo

- Docstring e comentário em português, tom informal (é como o resto do
  projeto já é escrito — lê qualquer arquivo em `src/jacarev3/` pra
  pegar o tom)
- Type hints em código novo (o projeto já tem 100% de cobertura —
  `mypy src/jacarev3` tem que continuar passando)
- Teste pra toda função nova que levanta erro ou faz cálculo — não
  precisa cobrir 100% de branch, mas o caminho principal e o de erro
  sim

## Documentação (`docs/`)

Todo tutorial em `docs/` segue a estrutura de 5 seções documentada em
`docs/index.md` ("Padrão dos tutoriais"). Se for escrever um tópico
novo, usa o mesmo formato.

## Abrindo a PR

Nada de processo formal — abre a PR, descreve o que mudou e por quê. Se
mexeu em opcode ou protocolo, cita a fonte na descrição também (além do
comentário no código). O CI roda sozinho; PR só é mergeada com CI verde.
