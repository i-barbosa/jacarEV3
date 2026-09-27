# Política de Segurança

## Escopo

`jacarev3` é uma lib educacional que fala com um EV3 físico via
Bluetooth ou USB, num contexto local (sala de aula, oficina). Não tem
servidor, não guarda credencial de ninguém, não expõe rede pra fora —
a superfície de ataque real é pequena, mas existe:

- Parsing de resposta do EV3 (`protocolo.parse_resposta`) — um EV3
  malicioso ou comprometido (ou um bug no parsing) poderia, em teoria,
  causar leitura fora dos limites de um buffer
- `jacarev3.fontes.FonteUDP` — recebe datagrama de rede sem autenticação
  nenhuma (por design: é um controle remoto local, não um serviço
  exposto — mas isso significa que qualquer coisa na mesma rede local
  pode mandar comando de movimento pro robô)

## Reportando uma vulnerabilidade

Abre uma issue **sem** detalhe técnico do problema, só avisando que tem
algo sensível a reportar, e pede contato privado — ou usa a aba
["Security" do GitHub](https://github.com/i-barbosa/jacarEV3/security)
pra reportar de forma privada direto pelo repositório.

Não existe programa de recompensa (é um projeto sem fins lucrativos),
mas todo relato é levado a sério e recebe resposta.

## Sem garantia de suporte a versões antigas

Projeto ainda pré-1.0, sem política formal de backport de correção de
segurança pra versão anterior — a orientação é sempre atualizar pra
última versão publicada no PyPI.
