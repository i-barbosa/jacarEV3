"""
jacarev3.robo
-----------
RoboEV3 — mesma API de antes (apitar, led, testar_motores, testar_sensores...)
mas agora rodando 100% no protocolo próprio (protocolo.py + conexao.py),
sem depender do pacote `ev3_dc` (GPLv3).

AVISO: primeira versão escrita do zero — os opcodes vêm da documentação
oficial da LEGO, mas ainda não foi validada em bateria extensa no robô
físico. Testa com calma e reporta qualquer comportamento estranho.
"""

from __future__ import annotations

import struct
import time
from typing import Any, Callable, Optional, Sequence, TypeVar, Union, overload

from . import protocolo as p
from .conexao import ConexaoBluetooth
from .erros import ErroDeParametro, ErroDePorta, ErroNoEV3
from .transporte import Transporte

_T = TypeVar("_T")

# 'A'-'D' pra motor; 1-4 pra sensor. Aceita qualquer coisa em tempo de
# execução (é o que permite a mensagem de erro amigável quando o tipo
# tá errado — ver _porta_motor/_porta_sensor) — por isso `object`, não
# `str`/`int`.
Porta = object

# porta -> apelido, ou porta -> (apelido, tipo de sensor: 'ultrassonico'/'toque'/'cor')
ConfigPorta = Union[str, tuple[str, str]]
MapaPortas = dict[object, ConfigPorta]

CORES_SENSOR = {
    0: 'nenhuma', 1: 'preto', 2: 'azul', 3: 'verde', 4: 'amarelo',
    5: 'vermelho', 6: 'branco', 7: 'marrom',
}

CODIGOS_LED = {
    'PRETO': p.LED_PRETO, 'DESLIGADO': p.LED_PRETO, 'OFF': p.LED_PRETO,
    'VERDE': p.LED_VERDE,
    'VERMELHO': p.LED_VERMELHO,
    'AMBAR': p.LED_AMBAR, 'LARANJA': p.LED_AMBAR,
    'VERDE_PISCA': p.LED_VERDE_PISCA,
    'VERMELHO_PISCA': p.LED_VERMELHO_PISCA,
    'AMBAR_PISCA': p.LED_AMBAR_PISCA,
    'VERDE_PULSA': p.LED_VERDE_PULSA,
    'VERMELHO_PULSA': p.LED_VERMELHO_PULSA,
    'AMBAR_PULSA': p.LED_AMBAR_PULSA,
}

PORTAS_MOTOR = {'A': p.PORTA_A, 'B': p.PORTA_B, 'C': p.PORTA_C, 'D': p.PORTA_D}
# Alguns opcodes querem o índice da porta (0-3) em vez do bitmask.
INDICES_MOTOR = {'A': p.INDICE_A, 'B': p.INDICE_B, 'C': p.INDICE_C, 'D': p.INDICE_D}
PORTAS_SENSOR = {1: 0, 2: 1, 3: 2, 4: 3}  # porta física -> índice interno (0-based)
TIPOS_SENSOR_VALIDOS = ('ultrassonico', 'toque', 'cor')


# ---------- Validação de porta/parâmetro (tolerante na forma, rígida na mensagem) ----------

def _parece_porta_motor(valor: object) -> bool:
    return isinstance(valor, str) and valor.upper() in PORTAS_MOTOR


def _parece_porta_sensor(valor: object) -> bool:
    if isinstance(valor, str) and valor.isdigit():
        valor = int(valor)
    return valor in PORTAS_SENSOR


def _porta_motor(porta: object) -> int:
    """'b' e 'B' viram o mesmo bitmask. Qualquer outra coisa levanta
    ErroDePorta com uma mensagem que ensina em vez de um KeyError cru."""
    if _parece_porta_motor(porta):
        assert isinstance(porta, str)
        return PORTAS_MOTOR[porta.upper()]
    dica = (
        " Motor usa letra ('A'-'D'); porta de sensor é que usa número (1-4)."
        if _parece_porta_sensor(porta) else " Use 'A', 'B', 'C' ou 'D'."
    )
    raise ErroDePorta(f"Porta de motor inválida: {porta!r}." + dica)


def _indice_motor(porta: object) -> int:
    if _parece_porta_motor(porta):
        assert isinstance(porta, str)
        return INDICES_MOTOR[porta.upper()]
    dica = (
        " Motor usa letra ('A'-'D'); porta de sensor é que usa número (1-4)."
        if _parece_porta_sensor(porta) else " Use 'A', 'B', 'C' ou 'D'."
    )
    raise ErroDePorta(f"Porta de motor inválida: {porta!r}." + dica)


def _porta_sensor(porta: object) -> int:
    """'1' (string) e 1 (int) viram o mesmo índice interno."""
    chave = int(porta) if isinstance(porta, str) and porta.isdigit() else porta
    if chave in PORTAS_SENSOR:
        return PORTAS_SENSOR[chave]
    dica = (
        " Sensor usa número (1-4); motor é que usa letra ('A'-'D')."
        if _parece_porta_motor(porta) else " Use 1, 2, 3 ou 4."
    )
    raise ErroDePorta(f"Porta de sensor inválida: {porta!r}." + dica)


def _validar_velocidade(velocidade: int) -> None:
    """girar_motor/mover_continuo/mover_base etc empacotam velocidade num
    DATA8 (-128 a 127) — mas o EV3 só entende -100 a 100 de verdade.
    Sem isso, velocidade=200 vira struct.error cru."""
    if not -100 <= velocidade <= 100:
        raise ErroDeParametro(f"velocidade={velocidade!r} fora da faixa -100 a 100.")


class RoboEV3:
    def __init__(
        self,
        mac: Optional[str] = None,
        canal: Optional[int] = None,
        timeout: float = 10,
        base: tuple[str, str] = ('B', 'C'),
        conexao: Optional[Transporte] = None,
        portas: Optional[MapaPortas] = None,
    ) -> None:
        """
        mac: endereço Bluetooth do EV3 (ex: '00:16:53:64:F8:B8')
        base: portas dos motores da base motriz (esquerda, direita)
        conexao: transporte pronto, no lugar do Bluetooth. Serve pra
                 testar a biblioteca sem robô ligado, e pra plugar outros
                 transportes (WiFi, USB) no futuro.
        portas: dict opcional mapeando porta -> apelido (ou porta -> (apelido, tipo)
                pra sensores), ex:
                {
                    'B': 'motor_esquerda', 'C': 'motor_direita',
                    1: ('sensor_cor', 'cor'),          # só testa tipo 'cor'
                    4: 'sensor_qualquer',               # testa os 3 tipos
                }
                Quando definido, testar_motores()/testar_sensores()/testar_tudo()
                só mexem nas portas listadas aqui. Sem isso, testam tudo
                (A-D, 1-4, todos os tipos) como sempre fizeram.
        """
        if conexao is None:
            if mac is None:
                raise ErroDeParametro("Informe o mac do EV3 ou uma conexao pronta")
            conexao = ConexaoBluetooth(mac, canal=canal, timeout=timeout)
        self.conexao: Transporte = conexao
        self.portas: MapaPortas = portas or {}
        self.base_esquerda: str
        self.base_direita: str
        self._base_bits: int
        self._base_invertida: bool
        self.definir_base(*base)

    def definir_base(self, esquerda: str = 'B', direita: str = 'C') -> None:
        """Define quais motores formam a base motriz (usada por mover_base).

        O firmware sempre trata o motor de porta mais baixa como o da
        esquerda. Se você montou ao contrário (esquerda em C, direita em
        B), a gente inverte o sinal da direção aqui pra que "direção
        positiva vira pra direita" continue valendo.
        """
        bit_esquerda = _porta_motor(esquerda)
        bit_direita = _porta_motor(direita)
        esquerda, direita = esquerda.upper(), direita.upper()
        if esquerda == direita:
            raise ErroDeParametro("A base precisa de dois motores diferentes")

        self.base_esquerda = esquerda
        self.base_direita = direita
        self._base_bits = bit_esquerda | bit_direita
        self._base_invertida = bit_esquerda > bit_direita

    def fechar(self) -> None:
        self.conexao.fechar()

    def __enter__(self) -> RoboEV3:
        return self

    def __exit__(self, *exc: object) -> None:
        self.fechar()

    # ---------- envio interno ----------

    def _enviar(
        self, comando: p.Comando, com_resposta: bool = False, bytes_globais: int = 0
    ) -> Optional[bytes]:
        contador = self.conexao.proximo_contador()
        pacote = comando.montar(contador, com_resposta=com_resposta, bytes_globais=bytes_globais)
        self.conexao.enviar(pacote)
        if com_resposta:
            dados = self.conexao.receber()
            _, ok, payload = p.parse_resposta(dados)
            if not ok:
                raise ErroNoEV3("EV3 respondeu com erro pro comando")
            return payload
        return None

    # ---------- Som / LED ----------

    def apitar(self, frequencia: int = 440, duracao_ms: int = 500, volume: int = 1) -> None:
        cmd = p.Comando().add(
            p.opSOUND, p.SOUND_TONE,
            p.lc_auto(volume), p.lc_auto(frequencia), p.lc_auto(duracao_ms),
        )
        self._enviar(cmd)

    def led(self, cor: str) -> None:
        codigo = CODIGOS_LED.get(cor.upper())
        if codigo is None:
            raise ErroDeParametro(f"Cor de LED desconhecida: {cor}. Opções: {list(CODIGOS_LED)}")
        cmd = p.Comando().add(p.opUI_WRITE, p.UI_WRITE_LED, p.lc0(codigo))
        self._enviar(cmd)

    # ---------- Espera por mudança (igual antes) ----------

    @staticmethod
    def espera_mudar(
        ler_valor: Callable[[], _T],
        tempo_limite: float = 15,
        intervalo: float = 0.2,
        formatar: Callable[[_T], str] = str,
        rotulo: str = "",
    ) -> bool:
        inicial = ler_valor()
        print(f"  Valor inicial{f' ({rotulo})' if rotulo else ''}: {formatar(inicial)}")
        inicio = time.time()
        while time.time() - inicio < tempo_limite:
            atual = ler_valor()
            if atual != inicial:
                print(f"  Mudou! {formatar(inicial)} -> {formatar(atual)}")
                return True
            time.sleep(intervalo)
        print(f"  [TIMEOUT] Nenhuma mudança em {tempo_limite}s.")
        return False

    # ---------- Motores ----------

    def girar_motor(
        self, porta: object, velocidade: int = 30, duracao_ms: int = 1000, frear: bool = True
    ) -> None:
        """
        Gira o motor por tempo (mais simples e robusto que graus/posição).
        velocidade: -100 a 100 (negativo = sentido contrário)
        """
        _validar_velocidade(velocidade)
        bit_porta = _porta_motor(porta)
        acao = p.PARAR_BRAKE if frear else p.PARAR_COAST
        cmd = p.Comando().add(
            p.opOUTPUT_TIME_SPEED,
            p.lc0(0),                    # layer 0
            p.lc0(bit_porta),            # porta
            p.lc1(velocidade),           # velocidade
            p.lc0(0),                    # step1 (ramp-up) = 0
            p.lc_auto(duracao_ms),       # step2 (duração em ms)
            p.lc0(0),                    # step3 (ramp-down) = 0
            p.lc0(acao),                 # ação ao parar
        )
        self._enviar(cmd)
        time.sleep(duracao_ms / 1000 + 0.1)

    def parar_motor(self, porta: object, frear: bool = True) -> None:
        bit_porta = _porta_motor(porta)
        acao = p.PARAR_BRAKE if frear else p.PARAR_COAST
        cmd = p.Comando().add(p.opOUTPUT_STOP, p.lc0(0), p.lc0(bit_porta), p.lc0(acao))
        self._enviar(cmd)

    def mover_continuo(self, porta: object, velocidade: int = 30) -> None:
        """
        Liga o motor numa velocidade e deixa rodando (não para sozinho).

        Usa opOUTPUT_SPEED (define a velocidade, com regulação) seguido de
        opOUTPUT_START (liga a partir dos valores atuais) — é o jeito que o
        firmware documenta pra movimento sem fim. Pra parar, chama
        parar_motor(). Serve pra loops de controle (seguir linha, desviar
        obstáculo) onde a velocidade muda a cada iteração.
        """
        _validar_velocidade(velocidade)
        bit_porta = _porta_motor(porta)
        cmd = p.Comando().add(
            p.opOUTPUT_SPEED, p.lc0(0), p.lc0(bit_porta), p.lc1(velocidade),
            p.opOUTPUT_START, p.lc0(0), p.lc0(bit_porta),
        )
        self._enviar(cmd)

    def girar_motor_graus(
        self,
        porta: object,
        graus: int,
        velocidade: int = 30,
        frear: bool = True,
        esperar: bool = True,
        rampa_graus: int = 0,
        tempo_limite: float = 30,
    ) -> None:
        """
        Gira o motor por uma quantidade exata de graus (usa o encoder).

        graus: quantos graus girar (sempre positivo)
        velocidade: -100 a 100 — o sinal decide o sentido
        rampa_graus: graus gastos acelerando e desacelerando, pra um
                     movimento mais suave
        esperar: se True, só retorna quando o motor terminar
        """
        if graus < 0:
            raise ErroDeParametro(
                "graus deve ser positivo — use velocidade negativa pra inverter o sentido"
            )
        _validar_velocidade(velocidade)

        bit_porta = _porta_motor(porta)
        acao = p.PARAR_BRAKE if frear else p.PARAR_COAST
        cmd = p.Comando().add(
            p.opOUTPUT_STEP_SPEED,
            p.lc0(0),                    # layer 0
            p.lc0(bit_porta),            # porta
            p.lc1(velocidade),           # velocidade
            p.lc_auto(rampa_graus),      # step1: rampa de subida
            p.lc_auto(graus),            # step2: graus em velocidade constante
            p.lc_auto(rampa_graus),      # step3: rampa de descida
            p.lc0(acao),                 # ação ao terminar
        )
        self._enviar(cmd)
        if esperar:
            self.esperar_motor(porta, tempo_limite=tempo_limite)

    def girar_motor_voltas(self, porta: object, voltas: float, **kwargs: Any) -> None:
        """Igual ao girar_motor_graus, mas contando voltas do eixo."""
        return self.girar_motor_graus(porta, round(voltas * 360), **kwargs)

    # ---------- Encoder e estado do motor ----------

    def motor_ocupado(self, porta: object) -> bool:
        """True enquanto o motor ainda está executando um comando."""
        bit_porta = _porta_motor(porta)
        cmd = p.Comando().add(
            p.opOUTPUT_TEST, p.lc0(0), p.lc0(bit_porta), p.gv0(0),
        )
        payload = self._enviar(cmd, com_resposta=True, bytes_globais=1)
        assert payload is not None
        return p.ler_int8(payload) != 0

    def esperar_motor(
        self, porta: object, tempo_limite: float = 30, intervalo: float = 0.05
    ) -> bool:
        """
        Bloqueia até o motor terminar o movimento atual.

        Pergunta pro EV3 de tempos em tempos em vez de usar opOUTPUT_READY,
        que travaria a VM do brick (e o socket) durante o movimento inteiro.
        Retorna False se estourar o tempo limite.
        """
        inicio = time.time()
        while time.time() - inicio < tempo_limite:
            if not self.motor_ocupado(porta):
                return True
            time.sleep(intervalo)
        return False

    def ler_graus_motor(self, porta: object) -> int:
        """Lê a contagem do encoder, em graus, desde o último zeramento."""
        indice = _indice_motor(porta)
        cmd = p.Comando().add(
            p.opOUTPUT_GET_COUNT, p.lc0(0), p.lc0(indice), p.gv0(0),
        )
        payload = self._enviar(cmd, com_resposta=True, bytes_globais=4)
        assert payload is not None
        return p.ler_int32(payload)

    def zerar_graus_motor(self, porta: object) -> None:
        """Zera a contagem do encoder do motor."""
        bit_porta = _porta_motor(porta)
        cmd = p.Comando().add(p.opOUTPUT_CLR_COUNT, p.lc0(0), p.lc0(bit_porta))
        self._enviar(cmd)

    # ---------- Base motriz (dois motores sincronizados) ----------

    def _direcao_valida(self, direcao: int) -> int:
        if not p.TURN_MIN <= direcao <= p.TURN_MAX:
            raise ErroDeParametro(
                f"direcao deve ficar entre {p.TURN_MIN} e {p.TURN_MAX}"
            )
        return -direcao if self._base_invertida else direcao

    def mover_base(
        self, velocidade: int = 30, direcao: int = 0, duracao_ms: int = 500, frear: bool = False
    ) -> None:
        """
        Move os dois motores da base sincronizados, por tempo.

        velocidade: -100 a 100 (negativo = ré)
        direcao: -200 a 200. 0 é reto, -100 para o motor esquerdo, +100
                 para o direito, ±200 gira no próprio eixo.
        duracao_ms: o EV3 para sozinho quando esse tempo acaba. É o que
                    torna essa função segura pra controle remoto: se o PC
                    morrer, o robô para em vez de sair correndo.

        Não bloqueia. Pra movimento contínuo, chama de novo antes do tempo
        acabar (ex: duracao_ms=400, reenviando a cada 100 ms).
        """
        _validar_velocidade(velocidade)
        acao = p.PARAR_BRAKE if frear else p.PARAR_COAST
        cmd = p.Comando().add(
            p.opOUTPUT_TIME_SYNC,
            p.lc0(0),                                  # layer 0
            p.lc0(self._base_bits),                    # os dois motores
            p.lc1(velocidade),                         # velocidade
            p.lc_auto(self._direcao_valida(direcao)),  # turn ratio
            p.lc_auto(duracao_ms),                     # tempo em ms
            p.lc0(acao),
        )
        self._enviar(cmd)

    def mover_base_graus(
        self,
        graus: int,
        velocidade: int = 30,
        direcao: int = 0,
        frear: bool = True,
        esperar: bool = True,
        tempo_limite: float = 30,
    ) -> None:
        """
        Move a base uma distância exata, contada em graus do motor.

        Mesma convenção de direção do mover_base. Com esperar=True, só
        retorna quando os motores pararem.
        """
        if graus < 0:
            raise ErroDeParametro(
                "graus deve ser positivo — use velocidade negativa pra dar ré"
            )
        _validar_velocidade(velocidade)

        acao = p.PARAR_BRAKE if frear else p.PARAR_COAST
        cmd = p.Comando().add(
            p.opOUTPUT_STEP_SYNC,
            p.lc0(0),
            p.lc0(self._base_bits),
            p.lc1(velocidade),
            p.lc_auto(self._direcao_valida(direcao)),
            p.lc_auto(graus),
            p.lc0(acao),
        )
        self._enviar(cmd)
        if esperar:
            self.esperar_motor(self.base_esquerda, tempo_limite=tempo_limite)

    def parar_base(self, frear: bool = True) -> None:
        """Para os dois motores da base de uma vez."""
        acao = p.PARAR_BRAKE if frear else p.PARAR_COAST
        cmd = p.Comando().add(
            p.opOUTPUT_STOP, p.lc0(0), p.lc0(self._base_bits), p.lc0(acao),
        )
        self._enviar(cmd)

    def testar_motor(self, porta: object, velocidade: int = 30, duracao_ms: int = 800) -> None:
        print(f"Girando motor {porta} pra frente...")
        self.girar_motor(porta, velocidade=velocidade, duracao_ms=duracao_ms)
        time.sleep(0.2)
        print(f"Girando motor {porta} pra trás...")
        self.girar_motor(porta, velocidade=-velocidade, duracao_ms=duracao_ms)

    # ---------- Portas configuradas ----------

    def _apelido(self, porta: object) -> Optional[str]:
        """Extrai o apelido de self.portas[porta], seja ele uma string
        solta ('nome') ou uma tupla ('nome', 'tipo')."""
        valor = self.portas.get(porta)
        if isinstance(valor, tuple):
            return valor[0]
        return valor

    def _tipo_sensor_configurado(self, porta: object) -> Optional[str]:
        """Retorna o tipo de sensor fixado ('ultrassonico'/'toque'/'cor')
        se a porta foi configurada como (apelido, tipo); None se não foi
        especificado (nesse caso testa_sensores testa os 3 tipos, como
        sempre fez)."""
        valor = self.portas.get(porta)
        if isinstance(valor, tuple) and len(valor) == 2:
            tipo = valor[1]
            if tipo not in TIPOS_SENSOR_VALIDOS:
                raise ErroDeParametro(
                    f"Tipo de sensor inválido pra porta {porta}: {tipo!r}. "
                    f"Use um de {TIPOS_SENSOR_VALIDOS}"
                )
            return tipo
        return None

    def _portas_motor_ativas(self) -> Sequence[object]:
        """Portas de motor a testar: as definidas em `portas`, ou todas
        (A-D) se nada foi configurado."""
        definidas = [porta for porta in self.portas if porta in PORTAS_MOTOR]
        return definidas or list(PORTAS_MOTOR)

    def _portas_sensor_ativas(self) -> Sequence[object]:
        """Portas de sensor a testar: as definidas em `portas`, ou todas
        (1-4) se nada foi configurado."""
        definidas = [porta for porta in self.portas if porta in PORTAS_SENSOR]
        return definidas or list(PORTAS_SENSOR)

    def testar_motores(self) -> None:
        print("========== TESTANDO MOTORES ==========\n")
        for letra in self._portas_motor_ativas():
            apelido = self._apelido(letra)
            rotulo = f"{letra} ({apelido})" if apelido else letra
            print(f"--- Motor na porta {rotulo} ---")
            try:
                self.testar_motor(letra)
                print(f"Motor {rotulo} OK!\n")
            except (ErroNoEV3, ErroDeParametro) as e:
                # ErroDeConexao NÃO é pego aqui — se o Bluetooth caiu, é
                # bem diferente de "não tem motor nessa porta", e precisa
                # parar o scan em vez de seguir reportando porta por porta.
                print(f"[AVISO] Sem motor (ou erro) na porta {rotulo}: {e}\n")

    # ---------- Sensores ----------

    @overload
    def _ler_sensor(self, indice_porta: int, modo: int) -> float: ...
    @overload
    def _ler_sensor(self, indice_porta: int, modo: int, n_valores: int) -> Union[float, tuple]: ...

    def _ler_sensor(
        self, indice_porta: int, modo: int, n_valores: int = 1
    ) -> Union[float, tuple]:
        cmd = p.Comando().add(
            p.opINPUT_DEVICE, p.INPUT_READY_SI,
            p.lc0(0),                # layer 0
            p.lc0(indice_porta),     # porta (0-3)
            p.lc0(0),                # DO_NOT_CHANGE_TYPE
            p.lc0(modo),             # modo
            p.lc0(n_valores),        # quantidade de valores
            p.gv0(0),                # onde guardar a resposta
        )
        payload = self._enviar(cmd, com_resposta=True, bytes_globais=4 * n_valores)
        assert payload is not None
        if n_valores == 1:
            return struct.unpack_from('<f', payload, 0)[0]
        return struct.unpack_from(f'<{n_valores}f', payload, 0)

    def ler_sensor(self, porta: object, modo: int) -> float:
        """
        Leitura direta e imediata de um sensor (sem esperar mudança) — pro
        uso em loops de controle (linha, obstáculo). `modo` vem das
        constantes MODO_* de jacarev3.protocolo (ex: p.MODO_COR_REFLETIDA).
        """
        indice = _porta_sensor(porta)
        return self._ler_sensor(indice, modo)

    def testar_ultrassonico(self, porta: object, tempo_limite: float = 15) -> None:
        indice = _porta_sensor(porta)
        self.espera_mudar(
            lambda: round(self._ler_sensor(indice, p.MODO_ULTRASSONICO_CM), 1),
            tempo_limite=tempo_limite,
            formatar=lambda v: f"{v} cm",
        )

    def testar_toque(self, porta: object, tempo_limite: float = 15) -> None:
        indice = _porta_sensor(porta)
        self.espera_mudar(
            lambda: self._ler_sensor(indice, p.MODO_TOQUE) > 0.5,
            tempo_limite=tempo_limite,
            formatar=lambda v: "pressionado" if v else "solto",
        )

    def testar_cor(self, porta: object, tempo_limite: float = 15) -> None:
        indice = _porta_sensor(porta)
        self.espera_mudar(
            lambda: round(self._ler_sensor(indice, p.MODO_COR_COR)),
            tempo_limite=tempo_limite,
            formatar=lambda v: CORES_SENSOR.get(v, f"desconhecida ({v})"),
        )

    def testar_sensores(
        self, tipos: tuple = ('ultrassonico', 'toque', 'cor'), tempo_limite: float = 15
    ) -> None:
        """
        tipos: quais tipos testar por padrão. Se uma porta específica foi
        configurada com (apelido, tipo), ela só é testada quando esse tipo
        estiver na rodada atual — as outras rodadas pulam ela.
        """
        metodos = {
            'ultrassonico': ('SENSORES ULTRASSÔNICOS', self.testar_ultrassonico),
            'toque': ('SENSORES DE TOQUE', self.testar_toque),
            'cor': ('SENSORES DE COR', self.testar_cor),
        }
        portas_ativas = self._portas_sensor_ativas()
        for tipo in tipos:
            titulo, metodo = metodos[tipo]
            print(f"========== TESTANDO {titulo} ==========\n")
            for numero in portas_ativas:
                tipo_fixado = self._tipo_sensor_configurado(numero)
                if tipo_fixado and tipo_fixado != tipo:
                    continue  # sensor tem tipo definido e não é esse agora
                apelido = self._apelido(numero)
                rotulo = f"{numero} ({apelido})" if apelido else numero
                print(f"--- {tipo} na porta {rotulo} ---")
                try:
                    metodo(numero, tempo_limite=tempo_limite)
                    print()
                except (ErroNoEV3, ErroDeParametro) as e:
                    # mesmo motivo do testar_motores: queda de conexão
                    # propaga em vez de virar "[AVISO] sem sensor".
                    print(f"[AVISO] Sem sensor (ou erro) na porta {rotulo}: {e}\n")

    def testar_tudo(self, tempo_limite: float = 15) -> None:
        self.testar_motores()
        self.testar_sensores(tempo_limite=tempo_limite)
        print("Teste completo finalizado.")
