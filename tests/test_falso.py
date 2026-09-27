"""
Testes do "robô de mentira" (jacarev3.falso.ConexaoFalsa) — o transporte
usado pra dar aula sem hardware.
"""

import pytest

from jacarev3 import protocolo as p
from jacarev3.falso import ConexaoFalsa
from jacarev3.robo import RoboEV3


@pytest.fixture
def robo():
    return RoboEV3(conexao=ConexaoFalsa(verboso=False))


def test_comandos_fire_and_forget_nao_quebram(robo):
    """apitar/led/girar_motor não esperam resposta — só não pode explodir."""
    robo.apitar()
    robo.led('VERDE')
    robo.girar_motor('B', velocidade=30, duracao_ms=1)
    robo.parar_motor('B')


def test_sensor_devolve_valor_padrao_sem_configuracao(robo):
    assert robo.ler_sensor(1, p.MODO_TOQUE) == pytest.approx(50.0)


def test_sensor_devolve_valor_configurado_por_porta_e_modo():
    conexao = ConexaoFalsa(
        valores_sensor={(0, p.MODO_ULTRASSONICO_CM): 12.5},  # porta física 1 = índice 0
        verboso=False,
    )
    robo = RoboEV3(conexao=conexao)
    assert robo.ler_sensor(1, p.MODO_ULTRASSONICO_CM) == pytest.approx(12.5)
    # outra porta/modo não configurados continuam no padrão
    assert robo.ler_sensor(2, p.MODO_TOQUE) == pytest.approx(50.0)


def test_sensor_aceita_funcao_dinamica():
    leituras = iter([10.0, 20.0, 30.0])
    conexao = ConexaoFalsa(
        valores_sensor={(0, p.MODO_COR_REFLETIDA): lambda porta, modo: next(leituras)},
        verboso=False,
    )
    robo = RoboEV3(conexao=conexao)
    valores = [robo.ler_sensor(1, p.MODO_COR_REFLETIDA) for _ in range(3)]
    assert valores == [10.0, 20.0, 30.0]


def test_encoder_e_motor_ocupado_devolvem_zero_por_padrao(robo):
    assert robo.ler_graus_motor('B') == 0
    assert robo.motor_ocupado('B') is False


def test_contador_incrementa_e_bate_na_resposta(robo):
    robo.apitar()
    valor1 = robo.ler_sensor(1, p.MODO_TOQUE)
    valor2 = robo.ler_sensor(1, p.MODO_TOQUE)
    assert valor1 == valor2 == pytest.approx(50.0)  # não levantou ErroDeProtocolo
    # 3 comandos mandados (apitar + 2 leituras), contador cresce a cada um
    assert len(robo.conexao.enviados) == 3


def test_verboso_imprime_algo_reconhecivel(capsys):
    robo = RoboEV3(conexao=ConexaoFalsa(verboso=True))
    robo.led('VERDE')
    saida = capsys.readouterr().out
    assert "LED" in saida


def test_testar_tudo_nao_quebra_sem_robo_de_verdade(monkeypatch):
    """Ponta a ponta: o fluxo mais comum de aula (testar_tudo) roda liso
    contra o robô de mentira, sem exceção nenhuma."""
    monkeypatch.setattr("jacarev3.robo.time.sleep", lambda *_: None)
    robo = RoboEV3(conexao=ConexaoFalsa(verboso=False))
    robo.testar_tudo(tempo_limite=0.05)
