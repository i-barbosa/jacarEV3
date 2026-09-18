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

import time
import struct

from . import protocolo as p
from .conexao import ConexaoBluetooth

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


class RoboEV3:
    def __init__(self, mac=None, canal=None, timeout=10, base=('B', 'C'),
                 conexao=None):
        """
        mac: endereço Bluetooth do EV3 (ex: '00:16:53:64:F8:B8')
        base: portas dos motores da base motriz (esquerda, direita)
        conexao: transporte pronto, no lugar do Bluetooth. Serve pra
                 testar a biblioteca sem robô ligado, e pra plugar outros
                 transportes (WiFi, USB) no futuro.
        """
        if conexao is None:
            if mac is None:
                raise ValueError("Informe o mac do EV3 ou uma conexao pronta")
            conexao = ConexaoBluetooth(mac, canal=canal, timeout=timeout)
        self.conexao = conexao
        self.definir_base(*base)

    def definir_base(self, esquerda='B', direita='C'):
        """Define quais motores formam a base motriz (usada por mover_base).

        O firmware sempre trata o motor de porta mais baixa como o da
        esquerda. Se você montou ao contrário (esquerda em C, direita em
        B), a gente inverte o sinal da direção aqui pra que "direção
        positiva vira pra direita" continue valendo.
        """
        for letra in (esquerda, direita):
            if letra not in PORTAS_MOTOR:
                raise ValueError(f"Porta de motor inválida: {letra}")
        if esquerda == direita:
            raise ValueError("A base precisa de dois motores diferentes")

        self.base_esquerda = esquerda
        self.base_direita = direita
        self._base_bits = PORTAS_MOTOR[esquerda] | PORTAS_MOTOR[direita]
        self._base_invertida = PORTAS_MOTOR[esquerda] > PORTAS_MOTOR[direita]

    def fechar(self):
        self.conexao.fechar()

    def __enter__(self):
        return self

    def __exit__(self, *exc):
        self.fechar()

    # ---------- envio interno ----------

    def _enviar(self, comando, com_resposta=False, bytes_globais=0):
        contador = self.conexao.proximo_contador()
        pacote = comando.montar(contador, com_resposta=com_resposta, bytes_globais=bytes_globais)
        self.conexao.enviar(pacote)
        if com_resposta:
            dados = self.conexao.receber()
            _, ok, payload = p.parse_resposta(dados)
            if not ok:
                raise RuntimeError("EV3 respondeu com erro pro comando")
            return payload
        return None

    # ---------- Som / LED ----------

    def apitar(self, frequencia=440, duracao_ms=500, volume=1):
        cmd = p.Comando().add(
            p.opSOUND, p.SOUND_TONE,
            p.lc_auto(volume), p.lc_auto(frequencia), p.lc_auto(duracao_ms),
        )
        self._enviar(cmd)

    def led(self, cor):
        codigo = CODIGOS_LED.get(cor.upper())
        if codigo is None:
            raise ValueError(f"Cor de LED desconhecida: {cor}. Opções: {list(CODIGOS_LED)}")
        cmd = p.Comando().add(p.opUI_WRITE, p.UI_WRITE_LED, p.lc0(codigo))
        self._enviar(cmd)

    # ---------- Espera por mudança (igual antes) ----------

    @staticmethod
    def espera_mudar(ler_valor, tempo_limite=15, intervalo=0.2, formatar=str, rotulo=""):
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

    def girar_motor(self, porta, velocidade=30, duracao_ms=1000, frear=True):
        """
        Gira o motor por tempo (mais simples e robusto que graus/posição).
        velocidade: -100 a 100 (negativo = sentido contrário)
        """
        bit_porta = PORTAS_MOTOR[porta]
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

    def parar_motor(self, porta, frear=True):
        bit_porta = PORTAS_MOTOR[porta]
        acao = p.PARAR_BRAKE if frear else p.PARAR_COAST
        cmd = p.Comando().add(p.opOUTPUT_STOP, p.lc0(0), p.lc0(bit_porta), p.lc0(acao))
        self._enviar(cmd)

    def mover_continuo(self, porta, velocidade=30):
        """
        Liga o motor numa velocidade e deixa rodando (não para sozinho).

        Usa opOUTPUT_SPEED (define a velocidade, com regulação) seguido de
        opOUTPUT_START (liga a partir dos valores atuais) — é o jeito que o
        firmware documenta pra movimento sem fim. Pra parar, chama
        parar_motor(). Serve pra loops de controle (seguir linha, desviar
        obstáculo) onde a velocidade muda a cada iteração.
        """
        bit_porta = PORTAS_MOTOR[porta]
        cmd = p.Comando().add(
            p.opOUTPUT_SPEED, p.lc0(0), p.lc0(bit_porta), p.lc1(velocidade),
            p.opOUTPUT_START, p.lc0(0), p.lc0(bit_porta),
        )
        self._enviar(cmd)

    def girar_motor_graus(self, porta, graus, velocidade=30, frear=True,
                          esperar=True, rampa_graus=0, tempo_limite=30):
        """
        Gira o motor por uma quantidade exata de graus (usa o encoder).

        graus: quantos graus girar (sempre positivo)
        velocidade: -100 a 100 — o sinal decide o sentido
        rampa_graus: graus gastos acelerando e desacelerando, pra um
                     movimento mais suave
        esperar: se True, só retorna quando o motor terminar
        """
        if graus < 0:
            raise ValueError(
                "graus deve ser positivo — use velocidade negativa pra inverter o sentido"
            )

        bit_porta = PORTAS_MOTOR[porta]
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

    def girar_motor_voltas(self, porta, voltas, **kwargs):
        """Igual ao girar_motor_graus, mas contando voltas do eixo."""
        return self.girar_motor_graus(porta, int(round(voltas * 360)), **kwargs)

    # ---------- Encoder e estado do motor ----------

    def motor_ocupado(self, porta):
        """True enquanto o motor ainda está executando um comando."""
        bit_porta = PORTAS_MOTOR[porta]
        cmd = p.Comando().add(
            p.opOUTPUT_TEST, p.lc0(0), p.lc0(bit_porta), p.gv0(0),
        )
        payload = self._enviar(cmd, com_resposta=True, bytes_globais=1)
        return p.ler_int8(payload) != 0

    def esperar_motor(self, porta, tempo_limite=30, intervalo=0.05):
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

    def ler_graus_motor(self, porta):
        """Lê a contagem do encoder, em graus, desde o último zeramento."""
        indice = INDICES_MOTOR[porta]
        cmd = p.Comando().add(
            p.opOUTPUT_GET_COUNT, p.lc0(0), p.lc0(indice), p.gv0(0),
        )
        payload = self._enviar(cmd, com_resposta=True, bytes_globais=4)
        return p.ler_int32(payload)

    def zerar_graus_motor(self, porta):
        """Zera a contagem do encoder do motor."""
        bit_porta = PORTAS_MOTOR[porta]
        cmd = p.Comando().add(p.opOUTPUT_CLR_COUNT, p.lc0(0), p.lc0(bit_porta))
        self._enviar(cmd)

    # ---------- Base motriz (dois motores sincronizados) ----------

    def _direcao_valida(self, direcao):
        if not p.TURN_MIN <= direcao <= p.TURN_MAX:
            raise ValueError(
                f"direcao deve ficar entre {p.TURN_MIN} e {p.TURN_MAX}"
            )
        return -direcao if self._base_invertida else direcao

    def mover_base(self, velocidade=30, direcao=0, duracao_ms=500, frear=False):
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

    def mover_base_graus(self, graus, velocidade=30, direcao=0, frear=True,
                         esperar=True, tempo_limite=30):
        """
        Move a base uma distância exata, contada em graus do motor.

        Mesma convenção de direção do mover_base. Com esperar=True, só
        retorna quando os motores pararem.
        """
        if graus < 0:
            raise ValueError(
                "graus deve ser positivo — use velocidade negativa pra dar ré"
            )

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

    def parar_base(self, frear=True):
        """Para os dois motores da base de uma vez."""
        acao = p.PARAR_BRAKE if frear else p.PARAR_COAST
        cmd = p.Comando().add(
            p.opOUTPUT_STOP, p.lc0(0), p.lc0(self._base_bits), p.lc0(acao),
        )
        self._enviar(cmd)

    def testar_motor(self, porta, velocidade=30, duracao_ms=800):
        print(f"Girando motor {porta} pra frente...")
        self.girar_motor(porta, velocidade=velocidade, duracao_ms=duracao_ms)
        time.sleep(0.2)
        print(f"Girando motor {porta} pra trás...")
        self.girar_motor(porta, velocidade=-velocidade, duracao_ms=duracao_ms)

    def testar_motores(self):
        print("========== TESTANDO MOTORES ==========\n")
        for letra in PORTAS_MOTOR:
            print(f"--- Motor na porta {letra} ---")
            try:
                self.testar_motor(letra)
                print(f"Motor {letra} OK!\n")
            except Exception as e:
                print(f"[AVISO] Sem motor (ou erro) na porta {letra}: {e}\n")

    # ---------- Sensores ----------

    def _ler_sensor(self, indice_porta, modo, n_valores=1):
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
        if n_valores == 1:
            return struct.unpack_from('<f', payload, 0)[0]
        return struct.unpack_from(f'<{n_valores}f', payload, 0)

    def ler_sensor(self, porta, modo):
        """
        Leitura direta e imediata de um sensor (sem esperar mudança) — pro
        uso em loops de controle (linha, obstáculo). `modo` vem das
        constantes MODO_* de jacarev3.protocolo (ex: p.MODO_COR_REFLETIDA).
        """
        indice = PORTAS_SENSOR[porta]
        return self._ler_sensor(indice, modo)

    def testar_ultrassonico(self, porta, tempo_limite=15):
        indice = PORTAS_SENSOR[porta]
        self.espera_mudar(
            lambda: round(self._ler_sensor(indice, p.MODO_ULTRASSONICO_CM), 1),
            tempo_limite=tempo_limite,
            formatar=lambda v: f"{v} cm",
        )

    def testar_toque(self, porta, tempo_limite=15):
        indice = PORTAS_SENSOR[porta]
        self.espera_mudar(
            lambda: self._ler_sensor(indice, p.MODO_TOQUE) > 0.5,
            tempo_limite=tempo_limite,
            formatar=lambda v: "pressionado" if v else "solto",
        )

    def testar_cor(self, porta, tempo_limite=15):
        indice = PORTAS_SENSOR[porta]
        self.espera_mudar(
            lambda: int(round(self._ler_sensor(indice, p.MODO_COR_COR))),
            tempo_limite=tempo_limite,
            formatar=lambda v: CORES_SENSOR.get(v, f"desconhecida ({v})"),
        )

    def testar_sensores(self, tipos=('ultrassonico', 'toque', 'cor'), tempo_limite=15):
        metodos = {
            'ultrassonico': ('SENSORES ULTRASSÔNICOS', self.testar_ultrassonico),
            'toque': ('SENSORES DE TOQUE', self.testar_toque),
            'cor': ('SENSORES DE COR', self.testar_cor),
        }
        for tipo in tipos:
            titulo, metodo = metodos[tipo]
            print(f"========== TESTANDO {titulo} ==========\n")
            for numero in PORTAS_SENSOR:
                print(f"--- {tipo} na porta {numero} ---")
                try:
                    metodo(numero, tempo_limite=tempo_limite)
                    print()
                except Exception as e:
                    print(f"[AVISO] Sem sensor (ou erro) na porta {numero}: {e}\n")

    def testar_tudo(self, tempo_limite=15):
        self.testar_motores()
        self.testar_sensores(tempo_limite=tempo_limite)
        print("Teste completo finalizado.")
