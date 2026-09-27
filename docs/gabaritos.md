# Respostas

Pelo menos 2 jeitos de resolver cada atividade de [Atividades](atividades.md).
Não é "o jeito certo" — é pra comparar com o que você fez e ver que tem
mais de um caminho válido.

Os trechos abaixo pressupõem que `robo` já é um `RoboEV3` conectado
(`with RoboEV3(...) as robo:`) e que `import time`,
`from jacarev3 import protocolo as p` e
`from jacarev3.topicos import circuito, desvio, controle` já foram
feitos, do jeito que os tutoriais ensinam.

## Básico

### Nível 1 — bipes em frequência/volume diferentes

=== "Jeito 1 — chamadas manuais"

    ```python
    robo.apitar(frequencia=220, volume=1)
    robo.apitar(frequencia=220, volume=25)
    robo.apitar(frequencia=220, volume=100)
    robo.apitar(frequencia=880, volume=25)
    robo.apitar(frequencia=1760, volume=25)
    ```

=== "Jeito 2 — varredura automática"

    ```python
    for freq in (220, 440, 880, 1760):
        for vol in (1, 25, 100):
            print(f"freq={freq} vol={vol}")
            robo.apitar(frequencia=freq, volume=vol, duracao_ms=300)
            time.sleep(0.5)
    ```

### Nível 2 — tabela de leituras por distância

=== "Jeito 1 — uma leitura por distância"

    ```python
    for d in (5, 10, 20, 40, 80):
        input(f"Posiciona o objeto a {d}cm e aperta Enter")
        print(f"{d}cm real -> lido {robo.ler_sensor(4, p.MODO_ULTRASSONICO_CM):.1f}cm")
    ```

=== "Jeito 2 — várias amostras, tira a média"

    ```python
    for d in (5, 10, 20, 40, 80):
        input(f"Posiciona o objeto a {d}cm e aperta Enter")
        amostras = [robo.ler_sensor(4, p.MODO_ULTRASSONICO_CM) for _ in range(5)]
        media = sum(amostras) / len(amostras)
        print(f"{d}cm real -> média de 5 leituras: {media:.1f}cm "
              f"(min {min(amostras):.1f}, max {max(amostras):.1f})")
    ```

### Nível 3 — contar apertos do sensor de toque

=== "Jeito 1 — flag de borda (polling)"

    ```python
    contagem = 0
    pressionado_antes = False
    while True:
        pressionado = robo.ler_sensor(2, p.MODO_TOQUE) > 0.5
        if pressionado and not pressionado_antes:
            contagem += 1
            print(f"Aperto número {contagem}")
        pressionado_antes = pressionado
        time.sleep(0.1)
    ```

=== "Jeito 2 — espera bloqueante por mudança"

    ```python
    def contar_toques(robo, porta=2, tempo_total=60):
        contagem = 0
        estado = robo.ler_sensor(porta, p.MODO_TOQUE) > 0.5
        inicio = time.time()
        while time.time() - inicio < tempo_total:
            restante = tempo_total - (time.time() - inicio)
            mudou = robo.espera_mudar(
                lambda: robo.ler_sensor(porta, p.MODO_TOQUE) > 0.5,
                tempo_limite=restante,
            )
            if not mudou:
                break
            estado = not estado
            if estado:  # virou True = acabou de ser pressionado
                contagem += 1
                print(f"Aperto número {contagem}")
        return contagem
    ```

    `espera_mudar` já existe na lib (usado por `testar_toque` por baixo
    dos panos) — aqui é só reaproveitado direto, sem escrever o loop de
    polling na mão.

### Nível 4 — "termômetro" de proximidade

=== "Jeito 1 — fórmula contínua"

    ```python
    while True:
        distancia = max(robo.ler_sensor(4, p.MODO_ULTRASSONICO_CM), 1)
        freq = min(3000, int(2000 / distancia))
        robo.led('VERMELHO' if distancia < 20 else 'VERDE')
        robo.apitar(frequencia=freq, duracao_ms=100, volume=10)
        time.sleep(max(0.05, distancia / 100))
    ```

=== "Jeito 2 — faixas discretas (bang-bang)"

    ```python
    while True:
        distancia = robo.ler_sensor(4, p.MODO_ULTRASSONICO_CM)
        if distancia < 10:
            robo.led('VERMELHO'); robo.apitar(frequencia=1800, duracao_ms=80); time.sleep(0.05)
        elif distancia < 30:
            robo.led('VERMELHO'); robo.apitar(frequencia=900, duracao_ms=80); time.sleep(0.2)
        elif distancia < 60:
            robo.led('AMBAR'); robo.apitar(frequencia=500, duracao_ms=80); time.sleep(0.4)
        else:
            robo.led('VERDE'); time.sleep(0.6)
    ```

    O jeito 1 é o mesmo tipo de controle **proporcional** do nível 4 de
    circuito; o jeito 2 é **bang-bang**, como o `seguir_linha` padrão —
    os dois nomes que você vai ver de novo lá.

## Seguir linha

### Nível 1 — comparar velocidades

=== "Jeito 1 — chamadas separadas"

    ```python
    circuito.seguir_linha(robo, porta_sensor=1, velocidade=15, duracao_s=15)
    circuito.seguir_linha(robo, porta_sensor=1, velocidade=25, duracao_s=15)
    circuito.seguir_linha(robo, porta_sensor=1, velocidade=40, duracao_s=15)
    ```

=== "Jeito 2 — loop com pausa pra reposicionar"

    ```python
    for v in (15, 25, 40):
        input(f"Testando velocidade={v} — reposiciona o robô e aperta Enter")
        circuito.seguir_linha(robo, porta_sensor=1, velocidade=v, duracao_s=15)
    ```

### Nível 2 — chute vs. calibrado

=== "Jeito 1 — só usar o calibrar()"

    ```python
    limiar = circuito.calibrar(robo, porta_sensor=1)
    print(f"Limiar calibrado: {limiar}")
    circuito.seguir_linha(robo, porta_sensor=1, limiar=limiar, velocidade=25)
    ```

=== "Jeito 2 — medir tempo de volta dos dois"

    ```python
    inicio = time.time()
    circuito.seguir_linha(robo, porta_sensor=1, limiar=50, duracao_s=20)  # chute
    tempo_chute = time.time() - inicio

    limiar = circuito.calibrar(robo, porta_sensor=1)
    inicio = time.time()
    circuito.seguir_linha(robo, porta_sensor=1, limiar=limiar, duracao_s=20)
    tempo_calibrado = time.time() - inicio

    print(f"Chute: {tempo_chute:.1f}s | Calibrado: {tempo_calibrado:.1f}s")
    ```

### Nível 3 — detectar linha perdida

=== "Jeito 1 — cronômetro (time.time)"

    ```python
    limiar = circuito.calibrar(robo, porta_sensor=1)
    ultimo_valor = None
    ultimo_tempo_mudou = time.time()

    while True:
        leitura = robo.ler_sensor(1, p.MODO_COR_REFLETIDA)
        if ultimo_valor is None or abs(leitura - ultimo_valor) > 2:
            ultimo_tempo_mudou = time.time()
        ultimo_valor = leitura

        if time.time() - ultimo_tempo_mudou > 2:
            robo.parar_motor('B'); robo.parar_motor('C')
            robo.apitar(); robo.apitar(); robo.apitar()
            print("Perdi a linha!")
            break

        if leitura > limiar:
            robo.mover_continuo('B', 25); robo.mover_continuo('C', 8)
        else:
            robo.mover_continuo('B', 8); robo.mover_continuo('C', 25)
        time.sleep(0.05)
    ```

=== "Jeito 2 — contador de iterações paradas"

    ```python
    limiar = circuito.calibrar(robo, porta_sensor=1)
    leituras_paradas = 0
    ultimo_valor = None

    while True:
        leitura = robo.ler_sensor(1, p.MODO_COR_REFLETIDA)
        if ultimo_valor is not None and abs(leitura - ultimo_valor) < 2:
            leituras_paradas += 1
        else:
            leituras_paradas = 0
        ultimo_valor = leitura

        if leituras_paradas > 40:  # 40 * 0.05s ≈ 2s
            robo.parar_motor('B'); robo.parar_motor('C')
            robo.apitar(); robo.apitar(); robo.apitar()
            print("Perdi a linha!")
            break

        if leitura > limiar:
            robo.mover_continuo('B', 25); robo.mover_continuo('C', 8)
        else:
            robo.mover_continuo('B', 8); robo.mover_continuo('C', 25)
        time.sleep(0.05)
    ```

    Os dois medem "faz tempo que não muda" — só que um mede tempo de
    verdade (`time.time()`) e o outro conta voltas do loop. O segundo é
    mais simples, mas quebra se o `time.sleep()` mudar de valor depois.

### Nível 4 — controle proporcional

=== "Jeito 1 — ganho fixo"

    ```python
    limiar = circuito.calibrar(robo, porta_sensor=1)
    velocidade_base = 30
    ganho = 0.6

    while True:
        leitura = robo.ler_sensor(1, p.MODO_COR_REFLETIDA)
        erro = leitura - limiar
        v_esquerda = velocidade_base + erro * ganho
        v_direita = velocidade_base - erro * ganho
        robo.mover_continuo('B', int(max(-100, min(100, v_esquerda))))
        robo.mover_continuo('C', int(max(-100, min(100, v_direita))))
        time.sleep(0.03)
    ```

=== "Jeito 2 — desacelera na curva"

    ```python
    limiar = circuito.calibrar(robo, porta_sensor=1)
    velocidade_base = 35
    ganho = 0.8

    while True:
        leitura = robo.ler_sensor(1, p.MODO_COR_REFLETIDA)
        erro = leitura - limiar
        curva = min(1.0, abs(erro) / 50)  # 0 (reto) a 1 (curva fechada)
        v = velocidade_base * (1 - 0.5 * curva)
        v_esquerda = v + erro * ganho
        v_direita = v - erro * ganho
        robo.mover_continuo('B', int(max(-100, min(100, v_esquerda))))
        robo.mover_continuo('C', int(max(-100, min(100, v_direita))))
        time.sleep(0.03)
    ```

    O jeito 2 é o exercício "curva mais fechada vs. reta" do próprio
    tutorial (seção 5) — dá pra sentir a diferença de estabilidade nas
    curvas fechadas.

## Desviar de obstáculo

### Nível 1 — comparar distância mínima

=== "Jeito 1 — chamadas separadas"

    ```python
    desvio.desviar_obstaculo(robo, porta_sensor=4, distancia_minima_cm=5, duracao_s=15)
    desvio.desviar_obstaculo(robo, porta_sensor=4, distancia_minima_cm=15, duracao_s=15)
    desvio.desviar_obstaculo(robo, porta_sensor=4, distancia_minima_cm=30, duracao_s=15)
    ```

=== "Jeito 2 — loop com pausa"

    ```python
    for d in (5, 15, 30):
        input(f"Testando distancia_minima_cm={d} — aperta Enter")
        desvio.desviar_obstaculo(robo, porta_sensor=4, distancia_minima_cm=d, duracao_s=15)
    ```

### Nível 2 — mapear a leitura do seu sensor montado

=== "Jeito 1 — só imprime"

    ```python
    while True:
        print(robo.ler_sensor(4, p.MODO_ULTRASSONICO_CM))
        time.sleep(0.2)
    ```

=== "Jeito 2 — guarda tudo e resume no final"

    ```python
    leituras = []
    inicio = time.time()
    while time.time() - inicio < 10:
        leituras.append(robo.ler_sensor(4, p.MODO_ULTRASSONICO_CM))
        time.sleep(0.2)

    print(f"Mínimo: {min(leituras):.1f}  Máximo: {max(leituras):.1f}  "
          f"Média: {sum(leituras)/len(leituras):.1f}")
    ```

### Nível 3 — contar obstáculos desviados

=== "Jeito 1 — borda de aproximação"

    ```python
    contagem = 0
    estava_perto = False
    inicio = time.time()

    while time.time() - inicio < 60:
        distancia = robo.ler_sensor(4, p.MODO_ULTRASSONICO_CM)
        perto = distancia < 15
        if perto and not estava_perto:
            contagem += 1
        estava_perto = perto
        # ... lógica de desvio de verdade entraria aqui
        time.sleep(0.1)

    print(f"Desviou de {contagem} obstáculos")
    ```

=== "Jeito 2 — cooldown entre contagens"

    ```python
    contagem = 0
    ultimo_desvio = 0
    inicio = time.time()

    while time.time() - inicio < 60:
        distancia = robo.ler_sensor(4, p.MODO_ULTRASSONICO_CM)
        agora = time.time()
        if distancia < 15 and (agora - ultimo_desvio) > 3:
            contagem += 1
            ultimo_desvio = agora
        # ... lógica de desvio de verdade entraria aqui
        time.sleep(0.1)

    print(f"Desviou de {contagem} obstáculos")
    ```

    O jeito 1 pode contar duas vezes o mesmo obstáculo se o robô oscilar
    perto do limite; o cooldown do jeito 2 evita isso — troca de
    complexidade por robustez.

### Nível 4 — seguir linha + desviar + reencontrar

=== "Jeito 1 — máquina de estados"

    ```python
    estado = 'seguindo'
    limiar = circuito.calibrar(robo, porta_sensor=1)

    while True:
        if estado == 'seguindo':
            if robo.ler_sensor(4, p.MODO_ULTRASSONICO_CM) < 15:
                robo.parar_motor('B'); robo.parar_motor('C')
                estado = 'desviando'
                continue
            leitura = robo.ler_sensor(1, p.MODO_COR_REFLETIDA)
            if leitura > limiar:
                robo.mover_continuo('B', 25); robo.mover_continuo('C', 8)
            else:
                robo.mover_continuo('B', 8); robo.mover_continuo('C', 25)

        elif estado == 'desviando':
            robo.mover_continuo('B', 25); robo.mover_continuo('C', -25)
            time.sleep(0.6)
            robo.mover_continuo('B', 25); robo.mover_continuo('C', 25)
            time.sleep(0.5)
            estado = 'procurando'

        elif estado == 'procurando':
            if robo.ler_sensor(1, p.MODO_COR_REFLETIDA) < limiar:
                estado = 'seguindo'
            else:
                robo.mover_continuo('B', 15); robo.mover_continuo('C', -15)

        time.sleep(0.05)
    ```

=== "Jeito 2 — função bloqueante, sem variável de estado"

    ```python
    def desviar_e_procurar(robo, limiar):
        robo.parar_motor('B'); robo.parar_motor('C')
        robo.mover_continuo('B', 25); robo.mover_continuo('C', -25)
        time.sleep(0.6)
        robo.mover_continuo('B', 25); robo.mover_continuo('C', 25)
        time.sleep(0.5)
        while robo.ler_sensor(1, p.MODO_COR_REFLETIDA) >= limiar:
            robo.mover_continuo('B', 15); robo.mover_continuo('C', -15)
            time.sleep(0.05)

    limiar = circuito.calibrar(robo, porta_sensor=1)
    while True:
        if robo.ler_sensor(4, p.MODO_ULTRASSONICO_CM) < 15:
            desviar_e_procurar(robo, limiar)
            continue
        leitura = robo.ler_sensor(1, p.MODO_COR_REFLETIDA)
        if leitura > limiar:
            robo.mover_continuo('B', 25); robo.mover_continuo('C', 8)
        else:
            robo.mover_continuo('B', 8); robo.mover_continuo('C', 25)
        time.sleep(0.05)
    ```

    O jeito 1 é explícito sobre "em qual fase eu tô" (bom quando o
    projeto cresce e ganha mais fases); o jeito 2 esconde a fase de
    desvio dentro de uma função que só volta quando termina — menos
    código, mas o loop principal não sabe que ela existe enquanto roda.

## Controle remoto

### Nível 1 — ajustar velocidade/giro

=== "Jeito 1 — editar e rodar de novo"

    ```python
    controle.controle_remoto(robo, velocidade=35, giro=100, verboso=True)
    # Ctrl+C, muda os números, roda de novo:
    controle.controle_remoto(robo, velocidade=50, giro=150, verboso=True)
    ```

=== "Jeito 2 — perguntar no terminal"

    ```python
    velocidade = int(input("velocidade (1-100): "))
    giro = int(input("giro (0-200): "))
    controle.controle_remoto(robo, velocidade=velocidade, giro=giro, verboso=True)
    ```

### Nível 2 — sentir zona morta e suavização

=== "Jeito 1 — um valor por vez"

    ```python
    from jacarev3.fontes import FontePygame

    with FontePygame(zona_morta_giro=0.3, taxa_suavizacao=0.05) as fonte:
        controle.controle_remoto(robo, fonte=fonte, verboso=True)
    ```

=== "Jeito 2 — cicla por presets, sem editar o arquivo"

    ```python
    from jacarev3.fontes import FontePygame

    presets = [
        {"zona_morta_giro": 0.0, "taxa_suavizacao": 1.0},   # cru, sem filtro
        {"zona_morta_giro": 0.3, "taxa_suavizacao": 0.05},  # bem suave e travado
        {"zona_morta_giro": 0.1, "taxa_suavizacao": 0.25},  # padrão, pra comparar
    ]

    for preset in presets:
        print(f"Testando: {preset}")
        with FontePygame(**preset) as fonte:
            controle.controle_remoto(robo, fonte=fonte, verboso=True)
        input("Enter pro próximo preset...")
    ```

### Nível 3 — um botão extra aciona LED/bipe

=== "Jeito 1 — loop próprio, à parte da lib"

    ```python
    import pygame

    pygame.init()
    pygame.joystick.init()
    joystick = pygame.joystick.Joystick(0)
    joystick.init()

    while True:
        pygame.event.pump()
        if joystick.get_button(3):  # botão Y, por exemplo — confere o seu
            robo.led('VERDE')
            robo.apitar()
        time.sleep(0.05)
    ```

=== "Jeito 2 — subclasse de FontePygame"

    ```python
    from jacarev3.fontes import FontePygame

    class FontePygameComBuzina(FontePygame):
        def __init__(self, robo, botao_buzina=3, **kwargs):
            super().__init__(**kwargs)
            self.robo = robo
            self.botao_buzina = botao_buzina

        def ler(self):
            if self._joystick.get_button(self.botao_buzina):
                self.robo.apitar()
            return super().ler()

    with FontePygameComBuzina(robo) as fonte:
        controle.controle_remoto(robo, fonte=fonte)
    ```

    O jeito 1 é o "hack rápido pra testar agora"; o jeito 2 é o jeito
    que se encaixa na arquitetura da lib — outro código que só use
    `fonte.ler()` (ex: gravar uma sessão de controle) já ganha a buzina
    de graça.

### Nível 4 — sua própria fonte

=== "Jeito 1 — FonteMouse (entrada ao vivo)"

    ```python
    import pygame
    from jacarev3.fontes import SAIR

    class FonteMouse:
        def __enter__(self):
            pygame.init()
            pygame.display.set_mode((300, 300))
            return self

        def __exit__(self, *exc):
            pygame.quit()
            return False

        def ler(self):
            for evento in pygame.event.get():
                if evento.type == pygame.QUIT:
                    return SAIR
            x, y = pygame.mouse.get_pos()
            velocidade = max(-1.0, min(1.0, (150 - y) / 150))
            giro = max(-1.0, min(1.0, (x - 150) / 150))
            return (velocidade, giro)

        def ajuda(self):
            return "Mouse: cima/baixo acelera/ré, esquerda/direita vira."
    ```

=== "Jeito 2 — FonteGravada (coreografia pronta)"

    ```python
    from jacarev3.fontes import SAIR

    class FonteGravada:
        """Reproduz uma sequência gravada: [(velocidade, direcao, passos), ...]"""

        def __init__(self, roteiro):
            self.roteiro = list(roteiro)
            self._indice = 0
            self._restantes = 0
            self._atual = (0, 0)

        def __enter__(self):
            return self

        def __exit__(self, *exc):
            return False

        def ler(self):
            if self._restantes <= 0:
                if self._indice >= len(self.roteiro):
                    return SAIR
                velocidade, direcao, passos = self.roteiro[self._indice]
                self._atual = (velocidade, direcao)
                self._restantes = passos
                self._indice += 1
            self._restantes -= 1
            return self._atual

        def ajuda(self):
            return "Reproduzindo uma coreografia gravada."

    roteiro = [(1, 0, 20), (1, 1, 10), (1, 0, 20), (0, 0, 5)]
    with FonteGravada(roteiro) as fonte:
        controle.controle_remoto(robo, fonte=fonte, intervalo=0.1)
    ```

    Os dois respeitam o mesmo contrato (`ler()` + `with`), mas servem
    pra coisas bem diferentes: uma é entrada humana ao vivo, a outra é
    automação sem humano nenhum no loop — o `controle_remoto()` não
    sabe (nem precisa saber) qual das duas tá rodando.
