## O que mudou e por quê

<!-- Descreve a mudança. Se for opcode/protocolo novo, cita a fonte
     (página do Communication Developer Kit, ou constante em bytecodes.h). -->

## Como testar

<!-- Como alguém revisando confirma que funciona, sem precisar de EV3 físico
     (a menos que só dê pra testar com hardware — nesse caso, diz isso). -->

## Checklist

- [ ] `pytest -q` passa
- [ ] `ruff check src/ tests/` passa
- [ ] `mypy src/jacarev3` passa
- [ ] Método/parâmetro novo tem nome em português
- [ ] Teste novo cobre o caminho principal (e o de erro, se aplicável)
- [ ] `CHANGELOG.md` atualizado, se a mudança for visível pro usuário
