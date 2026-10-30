#!/usr/bin/env python3
"""
Gera um diagrama SVG vetorial de altíssima precisão e sem alucinações
para a ligação direta entre o Raspberry Pi Pico e o leitor RFID MFRC522.
"""

def generate_svg():
    width = 1200
    height = 950

    svg = []
    svg.append(f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {width} {height}" width="100%" height="100%" style="background-color: #0f172a; font-family: -apple-system, BlinkMacSystemFont, Segoe UI, Roboto, Helvetica, Arial, sans-serif;">')

    # Defs para gradientes, sombras e marcadores
    svg.append('''
    <defs>
        <filter id="shadow" x="-5%" y="-5%" width="110%" height="110%">
            <feDropShadow dx="3" dy="5" stdDeviation="6" flood-color="#000000" flood-opacity="0.6"/>
        </filter>
        <linearGradient id="picoGrad" x1="0%" y1="0%" x2="100%" y2="100%">
            <stop offset="0%" stop-color="#059669"/>
            <stop offset="100%" stop-color="#047857"/>
        </linearGradient>
        <linearGradient id="rc522Grad" x1="0%" y1="0%" x2="100%" y2="100%">
            <stop offset="0%" stop-color="#1e3a8a"/>
            <stop offset="100%" stop-color="#1e40af"/>
        </linearGradient>
        <linearGradient id="chipGrad" x1="0%" y1="0%" x2="100%" y2="100%">
            <stop offset="0%" stop-color="#334155"/>
            <stop offset="100%" stop-color="#1e293b"/>
        </linearGradient>
    </defs>
    ''')

    # Cabeçalho do diagrama
    svg.append('''
    <rect width="100%" height="80" fill="#1e293b" />
    <text x="600" y="45" fill="#f8fafc" font-size="24" font-weight="bold" text-anchor="middle">DIAGRAMA DE LIGAÇÃO DIRETA: RASPBERRY PI PICO + RFID-RC522</text>
    <text x="600" y="68" fill="#94a3b8" font-size="14" text-anchor="middle">Sem protoboard • Ligação pino a pino com jumpers Fêmea-Macho • Comunicação SPI0 (3.3V)</text>
    ''')

    # ==========================================
    # 1. RASPBERRY PI PICO (LADO ESQUERDO)
    # ==========================================
    pico_x = 120
    pico_y = 130
    pico_w = 260
    pico_h = 750

    # Placa verde do Pico
    svg.append(f'''
    <!-- Raspberry Pi Pico PCB -->
    <rect x="{pico_x}" y="{pico_y}" width="{pico_w}" height="{pico_h}" rx="16" fill="url(#picoGrad)" stroke="#10b981" stroke-width="2" filter="url(#shadow)"/>
    
    <!-- Conector Micro-USB -->
    <rect x="{pico_x + 90}" y="{pico_y - 18}" width="80" height="26" rx="4" fill="#cbd5e1" stroke="#64748b" stroke-width="2"/>
    <rect x="{pico_x + 105}" y="{pico_y - 12}" width="50" height="14" rx="2" fill="#475569"/>
    <text x="{pico_x + 130}" y="{pico_y - 25}" fill="#94a3b8" font-size="12" font-weight="bold" text-anchor="middle">PORTA USB (TOPO)</text>
    
    <!-- Chip RP2040 -->
    <rect x="{pico_x + 85}" y="{pico_y + 280}" width="90" height="90" rx="8" fill="url(#chipGrad)" stroke="#475569" stroke-width="1.5"/>
    <text x="{pico_x + 130}" y="{pico_y + 325}" fill="#f8fafc" font-size="12" font-weight="bold" text-anchor="middle">RP2040</text>
    <text x="{pico_x + 130}" y="{pico_y + 342}" fill="#94a3b8" font-size="9" text-anchor="middle">Raspberry Pi</text>

    <!-- Botão BOOTSEL -->
    <rect x="{pico_x + 105}" y="{pico_y + 110}" width="50" height="30" rx="4" fill="#f8fafc" stroke="#94a3b8" stroke-width="1"/>
    <text x="{pico_x + 130}" y="{pico_y + 128}" fill="#0f172a" font-size="8" font-weight="bold" text-anchor="middle">BOOTSEL</text>

    <!-- Logo / Texto -->
    <text x="{pico_x + 130}" y="{pico_y + 70}" fill="#ecfdf5" font-size="16" font-weight="bold" text-anchor="middle">Raspberry Pi Pico</text>
    ''')

    # Dados exatos dos 40 pinos do Raspberry Pi Pico
    # Lado esquerdo: Pinos 1 a 20 (de cima para baixo)
    left_pins = [
        (1, "GP0"), (2, "GP1"), (3, "GND"), (4, "GP2"), (5, "GP3"),
        (6, "GP4"), (7, "GP5"), (8, "GND"), (9, "GP6"), (10, "GP7"),
        (11, "GP8"), (12, "GP9"), (13, "GND"), (14, "GP10"), (15, "GP11"),
        (16, "GP12"), (17, "GP13"), (18, "GND"), (19, "GP14"), (20, "GP15")
    ]

    # Lado direito: Pinos 40 a 21 (de cima para baixo)
    right_pins = [
        (40, "VBUS (5V)"), (39, "VSYS"), (38, "GND"), (37, "3V3_EN"), (36, "3V3 (OUT)"),
        (35, "ADC_VREF"), (34, "GP28"), (33, "GND"), (32, "GP27"), (31, "GP26"),
        (30, "RUN"), (29, "GP22"), (28, "GND"), (27, "GP21"), (26, "GP20"),
        (25, "GP19"), (24, "GP18"), (23, "GND"), (22, "GP17"), (21, "GP16")
    ]

    # Pinos destacados que conectam ao RFID
    highlight_pico = {
        36: ("#ef4444", "3.3V Power"),
        38: ("#475569", "Terra (GND)"),
        29: ("#f8fafc", "Reset (RST)"),
        25: ("#a855f7", "SPI0 TX (MOSI)"),
        24: ("#3b82f6", "SPI0 SCK (Clock)"),
        22: ("#22c55e", "SPI0 CS (SDA)"),
        21: ("#eab308", "SPI0 RX (MISO)")
    }

    pin_step = 34
    pin_start_y = pico_y + 40

    pico_pin_coords = {} # Guardar coordenadas para traçar as linhas

    # Desenhar pinos do lado esquerdo
    for i, (p_num, p_name) in enumerate(left_pins):
        y = pin_start_y + (i * pin_step)
        x = pico_x + 12
        pico_pin_coords[p_num] = (x, y)
        
        # Furo dourado
        svg.append(f'<circle cx="{x}" cy="{y}" r="6" fill="#fbbf24" stroke="#d97706" stroke-width="1"/>')
        svg.append(f'<circle cx="{x}" cy="{y}" r="3" fill="#0f172a"/>')
        # Rótulo
        svg.append(f'<text x="{x + 14}" y="{y + 4}" fill="#e2e8f0" font-size="11" font-weight="500">{p_name}</text>')
        svg.append(f'<text x="{x - 8}" y="{y + 4}" fill="#94a3b8" font-size="9" text-anchor="end">{p_num}</text>')

    # Desenhar pinos do lado direito
    for i, (p_num, p_name) in enumerate(right_pins):
        y = pin_start_y + (i * pin_step)
        x = pico_x + pico_w - 12
        pico_pin_coords[p_num] = (x, y)
        
        is_high = p_num in highlight_pico
        pad_fill = highlight_pico[p_num][0] if is_high else "#fbbf24"
        text_fill = "#ffffff" if is_high else "#e2e8f0"
        font_weight = "bold" if is_high else "500"

        # Furo
        svg.append(f'<circle cx="{x}" cy="{y}" r="6" fill="{pad_fill}" stroke="#d97706" stroke-width="1.5"/>')
        svg.append(f'<circle cx="{x}" cy="{y}" r="3" fill="#0f172a"/>')
        
        # Rótulo do pino
        svg.append(f'<text x="{x - 14}" y="{y + 4}" fill="{text_fill}" font-size="11" font-weight="{font_weight}" text-anchor="end">{p_name}</text>')
        svg.append(f'<text x="{x + 8}" y="{y + 4}" fill="#94a3b8" font-size="9">{p_num}</text>')

    # ==========================================
    # 2. MFRC522 RFID READER (LADO DIREITO)
    # ==========================================
    rc_x = 840
    rc_y = 230
    rc_w = 260
    rc_h = 520

    svg.append(f'''
    <!-- MFRC522 PCB -->
    <rect x="{rc_x}" y="{rc_y}" width="{rc_w}" height="{rc_h}" rx="12" fill="url(#rc522Grad)" stroke="#3b82f6" stroke-width="2" filter="url(#shadow)"/>

    <!-- Antena PCB (círculos concêntricos) -->
    <circle cx="{rc_x + rc_w/2}" cy="{rc_y + 350}" r="85" fill="none" stroke="#60a5fa" stroke-width="2" stroke-dasharray="4 2"/>
    <circle cx="{rc_x + rc_w/2}" cy="{rc_y + 350}" r="65" fill="none" stroke="#60a5fa" stroke-width="2"/>
    <circle cx="{rc_x + rc_w/2}" cy="{rc_y + 350}" r="45" fill="none" stroke="#60a5fa" stroke-width="2"/>
    <circle cx="{rc_x + rc_w/2}" cy="{rc_y + 350}" r="25" fill="none" stroke="#60a5fa" stroke-width="2"/>
    <text x="{rc_x + rc_w/2}" y="{rc_y + 355}" fill="#bfdbfe" font-size="14" font-weight="bold" text-anchor="middle">RFID-RC522</text>
    <text x="{rc_x + rc_w/2}" y="{rc_y + 375}" fill="#93c5fd" font-size="11" text-anchor="middle">13.56 MHz</text>

    <!-- Chip CI MFRC522 -->
    <rect x="{rc_x + 105}" y="{rc_y + 160}" width="50" height="50" rx="4" fill="url(#chipGrad)" stroke="#475569" stroke-width="1.5"/>
    <text x="{rc_x + 130}" y="{rc_y + 190}" fill="#f8fafc" font-size="9" font-weight="bold" text-anchor="middle">NXP</text>

    <!-- Barra preta dos conectores fêmea -->
    <rect x="{rc_x + 8}" y="{rc_y + 25}" width="24" height="230" rx="4" fill="#020617" stroke="#334155" stroke-width="1.5"/>
    ''')

    # Os 8 pinos do leitor RC522 (ordem física de cima para baixo)
    rc_pins = [
        ("SDA", "#22c55e", "GP17 (Pino 22)"),
        ("SCK", "#3b82f6", "GP18 (Pino 24)"),
        ("MOSI", "#a855f7", "GP19 (Pino 25)"),
        ("MISO", "#eab308", "GP16 (Pino 21)"),
        ("IRQ", "#64748b", "Não Conectado"),
        ("GND", "#475569", "GND (Pino 38)"),
        ("RST", "#f8fafc", "GP22 (Pino 29)"),
        ("3.3V", "#ef4444", "3V3 OUT (Pino 36)")
    ]

    rc_pin_coords = {}
    rc_step = 27
    rc_start_y = rc_y + 42

    for i, (p_name, color, dest) in enumerate(rc_pins):
        y = rc_start_y + (i * rc_step)
        x = rc_x + 20
        rc_pin_coords[p_name] = (x, y)
        
        # Pino macho dourado
        svg.append(f'<circle cx="{x}" cy="{y}" r="5" fill="#fbbf24" stroke="#d97706" stroke-width="1.5"/>')
        # Texto do pino na placa
        svg.append(f'<text x="{x + 22}" y="{y + 4}" fill="#ffffff" font-size="12" font-weight="bold">{p_name}</text>')

    # ==========================================
    # 3. LIGAÇÕES INDIVIDUAIS COM CABOS COLORIDOS
    # ==========================================
    connections = [
        # (Nome_RC, Pico_Pin, Cor, Label_Texto)
        ("3.3V", 36, "#ef4444", "1. Vermelho: 3.3V Power -> Pino 36 (3V3 OUT)"),
        ("GND",  38, "#94a3b8", "2. Preto: Terra (GND) -> Pino 38 (GND)"),
        ("RST",  29, "#f1f5f9", "3. Branco: Reset (RST) -> Pino 29 (GP22)"),
        ("MOSI", 25, "#c084fc", "4. Roxo: MOSI -> Pino 25 (GP19 - SPI0 TX)"),
        ("SCK",  24, "#60a5fa", "5. Azul: SCK -> Pino 24 (GP18 - SPI0 SCK)"),
        ("SDA",  22, "#4ade80", "6. Verde: SDA (CS) -> Pino 22 (GP17 - SPI0 CS)"),
        ("MISO", 21, "#facc15", "7. Amarelo: MISO -> Pino 21 (GP16 - SPI0 RX)")
    ]

    for rc_name, pico_pin, color, desc in connections:
        x_start, y_start = rc_pin_coords[rc_name]
        x_end, y_end = pico_pin_coords[pico_pin]

        # Ponto de controle da curva de Bezier cúbica para rota limpa
        dx = (x_start - x_end) * 0.45
        ctrl1_x = x_start - dx
        ctrl1_y = y_start
        ctrl2_x = x_end + dx
        ctrl2_y = y_end

        # Sombra do cabo
        svg.append(f'<path d="M {x_start} {y_start} C {ctrl1_x} {ctrl1_y}, {ctrl2_x} {ctrl2_y}, {x_end} {y_end}" fill="none" stroke="#000000" stroke-width="7" opacity="0.4"/>')
        
        # Cabo colorido com espessura realista
        svg.append(f'<path d="M {x_start} {y_start} C {ctrl1_x} {ctrl1_y}, {ctrl2_x} {ctrl2_y}, {x_end} {y_end}" fill="none" stroke="{color}" stroke-width="4.5" stroke-linecap="round"/>')

        # Conectores plásticos pretos nas pontas (representando pontas fêmea e macho dos jumpers)
        # Ponta Fêmea no RC522
        svg.append(f'<rect x="{x_start - 14}" y="{y_start - 6}" width="16" height="12" rx="2" fill="#0f172a" stroke="{color}" stroke-width="1.5"/>')
        # Ponta Macho no Pico
        svg.append(f'<rect x="{x_end - 2}" y="{y_end - 6}" width="16" height="12" rx="2" fill="#0f172a" stroke="{color}" stroke-width="1.5"/>')

    # ==========================================
    # 4. LEGENDA E QUADRO DE AVISOS NO RODAPÉ
    # ==========================================
    svg.append('''
    <!-- Legenda detalhada -->
    <rect x="420" y="130" width="380" height="320" rx="10" fill="#1e293b" stroke="#334155" stroke-width="1.5"/>
    <text x="610" y="160" fill="#38bdf8" font-size="14" font-weight="bold" text-anchor="middle">LEGENDA DOS 7 CABOS JUMPERS</text>
    ''')

    leg_y = 190
    for rc_name, pico_pin, color, desc in connections:
        svg.append(f'<circle cx="445" cy="{leg_y}" r="6" fill="{color}" stroke="#ffffff" stroke-width="1"/>')
        svg.append(f'<text x="465" y="{leg_y + 4}" fill="#f1f5f9" font-size="11.5" font-weight="500">{desc}</text>')
        leg_y += 32

    # Caixa de Alerta Vermelha
    svg.append('''
    <rect x="420" y="475" width="380" height="140" rx="10" fill="#450a0a" stroke="#ef4444" stroke-width="1.5"/>
    <text x="610" y="505" fill="#fca5a5" font-size="13" font-weight="bold" text-anchor="middle">⚠️ REGRA DE OURO DA ALIMENTAÇÃO</text>
    <text x="440" y="535" fill="#fef2f2" font-size="11.5">• O leitor opera estritamente a 3.3V.</text>
    <text x="440" y="560" fill="#fef2f2" font-size="11.5">• NUNCA ligue no Pino 40 (VBUS / 5V)!</text>
    <text x="440" y="585" fill="#fef2f2" font-size="11.5">• Ligue sempre no Pino 36 (3V3 OUT).</text>
    ''')

    # Caixa de instrução dos conectores
    svg.append('''
    <rect x="420" y="635" width="380" height="130" rx="10" fill="#0f172a" stroke="#38bdf8" stroke-width="1.5"/>
    <text x="610" y="665" fill="#38bdf8" font-size="13" font-weight="bold" text-anchor="middle">🔌 TIPO DE CONEXÃO DOS JUMPERS</text>
    <text x="440" y="695" fill="#e2e8f0" font-size="11.5">• Ponta FÊMEA: Encaixa nos pinos do RFID.</text>
    <text x="440" y="720" fill="#e2e8f0" font-size="11.5">• Ponta MACHO: Espeta nos furos do Pico.</text>
    <text x="440" y="745" fill="#e2e8f0" font-size="11.5">• Todos os 7 cabos vão para o LADO DIREITO!</text>
    ''')

    svg.append('</svg>')
    return '\n'.join(svg)

if __name__ == '__main__':
    svg_content = generate_svg()
    out_path = '/home/lirool/.gemini/antigravity-ide/scratch/Porta-LAOB/docs/images/diagrama_conexao_preciso.svg'
    with open(out_path, 'w', encoding='utf-8') as f:
        f.write(svg_content)
    print(f'Diagrama SVG gerado com sucesso em: {out_path}')
