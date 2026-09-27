<p align="center">
  <img src="https://raw.githubusercontent.com/i-barbosa/jacarEV3/main/assets/logo.png" width="150" alt="jacarEV3">
</p>

# jacarEV3 🐊

Lib em português pra controlar o LEGO EV3 via Bluetooth. Sem dependências
externas — só biblioteca padrão do Python.

[![PyPI](https://img.shields.io/pypi/v/jacarev3)](https://pypi.org/project/jacarev3/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://github.com/i-barbosa/jacarEV3/blob/main/LICENSE)

## Instalação

```bash
pip install jacarev3
```

## Uso rápido

```python
from jacarev3 import RoboEV3

with RoboEV3('00:16:53:64:F8:B8') as robo:  # MAC do seu EV3
    robo.apitar()
    robo.led('VERDE')
    robo.testar_tudo()  # testa motores A-D e sensores 1-4
```

## Documentação

Tutoriais passo a passo (som, LED, motor, sensor, seguir linha, desviar
de obstáculo) e a API completa estão no site:

**📖 [i-barbosa.github.io/jacarEV3](https://i-barbosa.github.io/jacarEV3/)**

## Contribuindo

Issues e PRs são bem-vindos em
[github.com/i-barbosa/jacarEV3](https://github.com/i-barbosa/jacarEV3).

## Licença

MIT — veja [LICENSE](https://github.com/i-barbosa/jacarEV3/blob/main/LICENSE).

## Colaboradores

<ul align="left">
  <li>Ítalo Vinicius (mantenedor) <a href="https://github.com/i-barbosa" target="_blank"><img src="https://img.shields.io/badge/GitHub-000000?style=for-the-badge&logo=github&logoColor=white" height="16"/></a></li>
  <li>Miguel Arcanjo <a href="https://github.com/MiguelAR098" target="_blank"><img src="https://img.shields.io/badge/GitHub-000000?style=for-the-badge&logo=github&logoColor=white" height="16"/></a></li>
  <li>Adrews <a href="https://github.com/Adrews1" target="_blank"><img src="https://img.shields.io/badge/GitHub-000000?style=for-the-badge&logo=github&logoColor=white" height="16"/></a></li>
</ul>

| Colaborador | Commits | Linhas | Contribuiu com |
| :--- | :---: | :--- | :--- |
| **Ítalo Vinicius** | 14 | +3520 / -323 | Protocolo próprio, `RoboEV3` base, hierarquia de erros, site de docs |
| **Miguel Arcanjo** | 2 | +1159 / -12 | Encoder, motor por graus, base motriz sincronizada, controle remoto |
| **Adrews** | 3 | +71 / -8 | Parâmetro `portas=` (apelido e filtro de porta em `testar_*`) |

Números de `git shortlog -sn` — mais em [CHANGELOG.md](https://github.com/i-barbosa/jacarEV3/blob/main/CHANGELOG.md).
