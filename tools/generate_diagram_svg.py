#!/usr/bin/env python3
"""
Gera um diagrama SVG vetorial de altíssima precisão e sem alucinações
para a ligação direta entre o Raspberry Pi Pico e o leitor RFID MFRC522.
Com roteamento ortogonal limpo e cantos arredondados, sem nenhuma ambiguidade.
"""

def make_ortho_path(x1, y1, x2, y2, x_turn, r=16):
    """Gera caminho SVG ortogonal com cantos arredondados (x1 > x2)."""
    dy = 1 if y2 > y1 else -1
    
    # Se a diferença em Y for menor que 2*r, ajusta o raio
    r_act = min(r, abs(y2 - y1) / 2.0, abs(x1 - x_turn) / 2.0, abs(x_turn - x2) / 2.0)
    
    path = []
    path.append(f"M {x1} {y1}")
    path.append(f"H {x_turn + r_act}")
    # Curva 1: virando na vertical
    path.append(f"Q {x_turn} {y1}, {x_turn} {y1 + dy * r_act}")
    path.append(f"V {y2 - dy * r_act}")
    # Curva 2: virando na horizontal para x2
    path.append(f"Q {x_turn} {y2}, {x_turn - r_act} {y2}")
    path.append(f"H {x2}")
    return " ".join(path)

def generate_svg():
    width = 1800
    height = 1100

    svg = []
    svg.append(f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {width} {height}" width="100%" height="100%" style="background-color: #0b1120; font-family: -apple-system, BlinkMacSystemFont, Segoe UI, Roboto, Helvetica, Arial, sans-serif;">')

    # Defs
    svg.append('''
    <defs>
        <filter id="shadow" x="-5%" y="-5%" width="110%" height="110%">
            <feDropShadow dx="4" dy="6" stdDeviation="8" flood-color="#000000" flood-opacity="0.6"/>
        </filter>
        <filter id="badgeShadow" x="-10%" y="-10%" width="120%" height="120%">
            <feDropShadow dx="2" dy="3" stdDeviation="3" flood-color="#000000" flood-opacity="0.5"/>
        </filter>
        <linearGradient id="picoGrad" x1="0%" y1="0%" x2="100%" y2="100%">
            <stop offset="0%" stop-color="#065f46"/>
            <stop offset="50%" stop-color="#047857"/>
            <stop offset="100%" stop-color="#064e3b"/>
        </linearGradient>
        <linearGradient id="rc522Grad" x1="0%" y1="0%" x2="100%" y2="100%">
            <stop offset="0%" stop-color="#1e3a8a"/>
            <stop offset="60%" stop-color="#1d4ed8"/>
            <stop offset="100%" stop-color="#172554"/>
        </linearGradient>
        <linearGradient id="chipGrad" x1="0%" y1="0%" x2="100%" y2="100%">
            <stop offset="0%" stop-color="#334155"/>
            <stop offset="100%" stop-color="#0f172a"/>
        </linearGradient>
        <linearGradient id="panelGrad" x1="0%" y1="0%" x2="0%" y2="100%">
            <stop offset="0%" stop-color="#1e293b"/>
            <stop offset="100%" stop-color="#0f172a"/>
        </linearGradient>
    </defs>
    ''')

    # Cabeçalho
    svg.append('''
    <rect width="100%" height="84" fill="#0f172a" stroke="#1e293b" stroke-width="2"/>
    <rect x="0" y="80" width="100%" height="4" fill="#38bdf8"/>
    <text x="900" y="44" fill="#f8fafc" font-size="24" font-weight="800" text-anchor="middle" letter-spacing="0.5">DIAGRAMA OFICIAL DE LIGAÇÃO DIRETA: RASPBERRY PI PICO ↔ RFID-RC522</text>
    <text x="900" y="70" fill="#94a3b8" font-size="14" text-anchor="middle">Sem Protoboard • 7 Cabos Jumpers Fêmea-Macho • Mapeamento SPI0 Oficial • 100% Validado com o Código MicroPython</text>
    ''')

    # 1. PICO
    pico_x = 65
    pico_y = 125
    pico_w = 300
    pico_h = 920

    svg.append(f'''
    <!-- Raspberry Pi Pico PCB -->
    <rect x="{pico_x}" y="{pico_y}" width="{pico_w}" height="{pico_h}" rx="18" fill="url(#picoGrad)" stroke="#10b981" stroke-width="2.5" filter="url(#shadow)"/>
    
    <!-- Conector Micro-USB -->
    <rect x="{pico_x + 110}" y="{pico_y - 18}" width="80" height="26" rx="4" fill="#cbd5e1" stroke="#64748b" stroke-width="2"/>
    <rect x="{pico_x + 125}" y="{pico_y - 12}" width="50" height="14" rx="2" fill="#334155"/>
    <text x="{pico_x + 150}" y="{pico_y - 25}" fill="#94a3b8" font-size="11" font-weight="bold" text-anchor="middle">MICRO-USB (TOPO)</text>
    
    <!-- Chip RP2040 -->
    <rect x="{pico_x + 105}" y="{pico_y + 380}" width="90" height="90" rx="8" fill="url(#chipGrad)" stroke="#64748b" stroke-width="1.5"/>
    <text x="{pico_x + 150}" y="{pico_y + 425}" fill="#f8fafc" font-size="13" font-weight="bold" text-anchor="middle">RP2040</text>
    <text x="{pico_x + 150}" y="{pico_y + 444}" fill="#94a3b8" font-size="10" text-anchor="middle">Raspberry Pi</text>

    <!-- Botão BOOTSEL -->
    <rect x="{pico_x + 125}" y="{pico_y + 130}" width="50" height="28" rx="4" fill="#f8fafc" stroke="#94a3b8" stroke-width="1"/>
    <text x="{pico_x + 150}" y="{pico_y + 148}" fill="#0f172a" font-size="8.5" font-weight="bold" text-anchor="middle">BOOTSEL</text>

    <!-- Título do Pico -->
    <text x="{pico_x + 150}" y="{pico_y + 75}" fill="#ecfdf5" font-size="17" font-weight="800" text-anchor="middle">Raspberry Pi Pico</text>
    <text x="{pico_x + 150}" y="{pico_y + 96}" fill="#a7f3d0" font-size="11" text-anchor="middle">Pinagem Oficial RP2040</text>
    ''')

    left_pins = [
        (1, "GP0"), (2, "GP1"), (3, "GND"), (4, "GP2"), (5, "GP3"),
        (6, "GP4"), (7, "GP5"), (8, "GND"), (9, "GP6"), (10, "GP7"),
        (11, "GP8"), (12, "GP9"), (13, "GND"), (14, "GP10"),
        (15, "GP11 (Sensor)"),
        (16, "GP12 (Buzzer)"),
        (17, "GP13 (Botão)"),
        (18, "GND"),
        (19, "GP14 (IRQ opc.)"),
        (20, "GP15 [RELÉ]")
    ]

    right_pins = [
        (40, "VBUS (5V - NÃO USAR)", "#ef4444"),
        (39, "VSYS", None),
        (38, "GND ★", "#475569"),
        (37, "3V3_EN", None),
        (36, "3V3 OUT ★", "#ef4444"),
        (35, "ADC_VREF", None),
        (34, "GP28", None),
        (33, "GND", None),
        (32, "GP27", None),
        (31, "GP26", None),
        (30, "RUN", None),
        (29, "GP22 (RST) ★", "#f1f5f9"),
        (28, "GND", None),
        (27, "GP21", None),
        (26, "GP20", None),
        (25, "GP19 (MOSI) ★", "#c084fc"),
        (24, "GP18 (SCK) ★", "#60a5fa"),
        (23, "GND", None),
        (22, "GP17 (SDA/CS) ★", "#4ade80"),
        (21, "GP16 (MISO) ★", "#facc15")
    ]

    pico_pin_coords = {}
    pin_step = 38.5
    pin_start_y = pico_y + 175

    for i, (p_num, p_name) in enumerate(left_pins):
        y = pin_start_y + (i * pin_step)
        x = pico_x + 14
        pico_pin_coords[p_num] = (x, y)
        is_irq = (p_num == 19)
        is_rele = (p_num == 20)
        pad_fill = "#64748b" if is_irq else ("#f97316" if is_rele else "#fbbf24")
        pad_stroke = "#ffffff" if (is_irq or is_rele) else "#d97706"
        svg.append(f'<circle cx="{x}" cy="{y}" r="6" fill="{pad_fill}" stroke="{pad_stroke}" stroke-width="1.5"/>')
        svg.append(f'<circle cx="{x}" cy="{y}" r="2.5" fill="#0f172a"/>')
        label_color = "#ffffff" if (is_irq or is_rele) else "#cbd5e1"
        weight = "bold" if (is_irq or is_rele) else "500"
        svg.append(f'<text x="{x + 14}" y="{y + 4}" fill="{label_color}" font-size="10.5" font-weight="{weight}">{p_name}</text>')
        svg.append(f'<text x="{x - 8}" y="{y + 4}" fill="#94a3b8" font-size="9" text-anchor="end">{p_num}</text>')

    for i, (p_num, p_name, color) in enumerate(right_pins):
        y = pin_start_y + (i * pin_step)
        x = pico_x + pico_w - 14
        pico_pin_coords[p_num] = (x, y)
        is_rfid = color is not None
        pad_fill = color if is_rfid else "#fbbf24"
        pad_stroke = "#ffffff" if is_rfid else "#d97706"
        text_fill = "#ffffff" if is_rfid else "#cbd5e1"
        font_weight = "bold" if is_rfid else "500"
        svg.append(f'<circle cx="{x}" cy="{y}" r="6.5" fill="{pad_fill}" stroke="{pad_stroke}" stroke-width="1.5"/>')
        svg.append(f'<circle cx="{x}" cy="{y}" r="2.5" fill="#0f172a"/>')
        svg.append(f'<text x="{x - 14}" y="{y + 4}" fill="{text_fill}" font-size="10.5" font-weight="{font_weight}" text-anchor="end">{p_name}</text>')
        svg.append(f'<text x="{x + 9}" y="{y + 4}" fill="#94a3b8" font-size="9">{p_num}</text>')


    # 2. MFRC522 RFID READER
    rc_x = 880
    rc_y = 125
    rc_w = 260
    rc_h = 920

    svg.append(f'''
    <!-- MFRC522 PCB -->
    <rect x="{rc_x}" y="{rc_y}" width="{rc_w}" height="{rc_h}" rx="16" fill="url(#rc522Grad)" stroke="#3b82f6" stroke-width="2.5" filter="url(#shadow)"/>

    <!-- Título do Leitor no topo da placa -->
    <text x="{rc_x + rc_w/2}" y="{rc_y + 36}" fill="#f8fafc" font-size="15" font-weight="bold" text-anchor="middle">MÓDULO LEITOR RFID</text>
    <text x="{rc_x + rc_w/2}" y="{rc_y + 56}" fill="#93c5fd" font-size="12" text-anchor="middle">MFRC522 (3.3V SPI)</text>
    <line x1="{rc_x + 20}" y1="{rc_y + 68}" x2="{rc_x + rc_w - 20}" y2="{rc_y + 68}" stroke="#3b82f6" stroke-width="1" opacity="0.6"/>

    <!-- Barra preta dos 8 pinos do cabeçalho -->
    <rect x="{rc_x + 12}" y="{rc_y + 80}" width="26" height="360" rx="4" fill="#020617" stroke="#334155" stroke-width="1.5"/>

    <!-- Antena PCB concêntrica no terço inferior -->
    <circle cx="{rc_x + rc_w/2}" cy="{rc_y + 700}" r="95" fill="none" stroke="#60a5fa" stroke-width="2.5" stroke-dasharray="5 3"/>
    <circle cx="{rc_x + rc_w/2}" cy="{rc_y + 700}" r="75" fill="none" stroke="#60a5fa" stroke-width="2"/>
    <circle cx="{rc_x + rc_w/2}" cy="{rc_y + 700}" r="55" fill="none" stroke="#60a5fa" stroke-width="2"/>
    <circle cx="{rc_x + rc_w/2}" cy="{rc_y + 700}" r="35" fill="none" stroke="#60a5fa" stroke-width="2"/>
    <circle cx="{rc_x + rc_w/2}" cy="{rc_y + 700}" r="15" fill="none" stroke="#60a5fa" stroke-width="2"/>
    <text x="{rc_x + rc_w/2}" y="{rc_y + 705}" fill="#bfdbfe" font-size="15" font-weight="bold" text-anchor="middle">RFID-RC522</text>
    <text x="{rc_x + rc_w/2}" y="{rc_y + 727}" fill="#93c5fd" font-size="11.5" text-anchor="middle">13.56 MHz SPI</text>

    <!-- Chip CI MFRC522 -->
    <rect x="{rc_x + 105}" y="{rc_y + 480}" width="50" height="50" rx="4" fill="url(#chipGrad)" stroke="#475569" stroke-width="1.5"/>
    <text x="{rc_x + 130}" y="{rc_y + 510}" fill="#f8fafc" font-size="9" font-weight="bold" text-anchor="middle">NXP</text>
    ''')

    rc_pins = [
        ("SDA",  "#4ade80", "Chip Select (CSn)"),
        ("SCK",  "#60a5fa", "Clock SPI"),
        ("MOSI", "#c084fc", "Master Out (TX)"),
        ("MISO", "#facc15", "Master In (RX)"),
        ("IRQ",  "#64748b", "Interrupção (Opc.)"),
        ("GND",  "#94a3b8", "Terra / Negativo"),
        ("RST",  "#f1f5f9", "Reset do Leitor"),
        ("3.3V", "#ef4444", "Alimentação 3.3V")
    ]

    rc_pin_coords = {}
    rc_start_y = rc_y + 105
    rc_step = 42

    for i, (p_name, color, func) in enumerate(rc_pins):
        y = rc_start_y + (i * rc_step)
        x = rc_x + 25
        rc_pin_coords[p_name] = (x, y)
        svg.append(f'<circle cx="{x}" cy="{y}" r="6" fill="{color}" stroke="#ffffff" stroke-width="1.5"/>')
        svg.append(f'<text x="{x + 24}" y="{y + 4}" fill="#ffffff" font-size="12.5" font-weight="bold">{p_name}</text>')
        svg.append(f'<text x="{x + 85}" y="{y + 4}" fill="#93c5fd" font-size="10.5">({func})</text>')


    # 3. LIGAÇÕES INDIVIDUAIS COM CABOS COLORIDOS (ROTEAMENTO ORTOGONAL LIMPO)
    # Lista de conexões: (rc_name, pico_pin, cor, x_turn, label_badge)
    connections = [
        ("3.3V", 36, "#ef4444", 760, "3.3V"),
        ("GND",  38, "#94a3b8", 810, "GND"),
        ("RST",  29, "#f1f5f9", 710, "RST"),
        ("MOSI", 25, "#c084fc", 660, "MOSI"),
        ("SCK",  24, "#60a5fa", 610, "SCK"),
        ("SDA",  22, "#4ade80", 560, "SDA"),
        ("MISO", 21, "#facc15", 510, "MISO"),
    ]

    pico_conn_x = pico_x + pico_w - 14  # x=351

    for rc_name, pico_pin, color, x_turn, badge_text in connections:
        x_start, y_start = rc_pin_coords[rc_name]
        x_end, y_end = pico_pin_coords[pico_pin]

        # Caminho ortogonal com cantos arredondados
        path_d = make_ortho_path(x_start, y_start, x_end, y_end, x_turn, r=16)

        # Sombra
        svg.append(f'<path d="{path_d}" fill="none" stroke="#000000" stroke-width="8" opacity="0.45" stroke-linecap="round" stroke-linejoin="round"/>')
        
        # Fio colorido
        svg.append(f'<path d="{path_d}" fill="none" stroke="{color}" stroke-width="4.5" stroke-linecap="round" stroke-linejoin="round"/>')

        # Conector Plástico Fêmea no RC522
        svg.append(f'<rect x="{x_start - 18}" y="{y_start - 6}" width="18" height="12" rx="2.5" fill="#0f172a" stroke="{color}" stroke-width="1.8"/>')
        
        # Conector Plástico Macho no Pico
        svg.append(f'<rect x="{x_end}" y="{y_end - 6}" width="18" height="12" rx="2.5" fill="#0f172a" stroke="{color}" stroke-width="1.8"/>')

        # Badge indicador no segmento horizontal que chega ao Pico (em x=415)
        badge_w = 58
        badge_h = 20
        badge_x = 405
        badge_y = y_end - 10
        svg.append(f'''
        <g transform="translate({badge_x}, {badge_y})">
            <rect width="{badge_w}" height="{badge_h}" rx="4" fill="#0f172a" stroke="{color}" stroke-width="1.8" filter="url(#badgeShadow)"/>
            <text x="{badge_w/2}" y="14" fill="{color}" font-size="10.5" font-weight="bold" text-anchor="middle">{badge_text}</text>
        </g>
        ''')

    # Fio opcional de IRQ (GP14) - Rota elegante por baixo
    rc_irq_x, rc_irq_y = rc_pin_coords["IRQ"]
    pico_irq_x, pico_irq_y = pico_pin_coords[19] # GP14
    
    irq_path = f"M {rc_irq_x} {rc_irq_y} H 470 V 1045 H {pico_irq_x - 30} V {pico_irq_y} H {pico_irq_x}"
    svg.append(f'''
    <!-- Fio IRQ opcional tracejado -->
    <path d="{irq_path}" fill="none" stroke="#000000" stroke-width="5" opacity="0.3"/>
    <path d="{irq_path}" fill="none" stroke="#64748b" stroke-width="2.5" stroke-dasharray="8 5" stroke-linejoin="round"/>
    <rect x="{rc_irq_x - 18}" y="{rc_irq_y - 6}" width="18" height="12" rx="2" fill="#0f172a" stroke="#64748b" stroke-width="1.5"/>
    <rect x="{pico_irq_x - 18}" y="{pico_irq_y - 6}" width="18" height="12" rx="2" fill="#0f172a" stroke="#64748b" stroke-width="1.5"/>
    <rect x="230" y="1035" width="220" height="20" rx="4" fill="#0f172a" stroke="#64748b" stroke-width="1.5"/>
    <text x="340" y="1049" fill="#94a3b8" font-size="10" font-weight="bold" text-anchor="middle">Fio Cinza IRQ (Opcional) → Pino 19 (GP14)</text>
    ''')


    # 4. PAINEL LATERAL INFORMATIVO (LADO DIREITO: x=1180 a 1760)
    pan_x = 1180
    pan_y = 125
    pan_w = 580
    pan_h = 920

    svg.append(f'''
    <!-- Fundo do Painel Lateral -->
    <rect x="{pan_x}" y="{pan_y}" width="{pan_w}" height="{pan_h}" rx="16" fill="url(#panelGrad)" stroke="#334155" stroke-width="2" filter="url(#shadow)"/>

    <!-- Título do Painel -->
    <rect x="{pan_x}" y="{pan_y}" width="{pan_w}" height="48" rx="16" fill="#1e293b"/>
    <rect x="{pan_x}" y="{pan_y + 36}" width="{pan_w}" height="12" fill="#1e293b"/>
    <text x="{pan_x + pan_w/2}" y="{pan_y + 31}" fill="#38bdf8" font-size="15" font-weight="800" text-anchor="middle" letter-spacing="0.5">TABELA DE CONEXÕES DIRETAS (SEM PROTOBOARD)</text>
    ''')

    # Cabeçalho da Tabela
    tab_y = pan_y + 68
    svg.append(f'''
    <!-- Cabeçalho da Tabela -->
    <rect x="{pan_x + 16}" y="{tab_y}" width="{pan_w - 32}" height="32" rx="6" fill="#0f172a" stroke="#334155" stroke-width="1"/>
    <text x="{pan_x + 35}" y="{tab_y + 20}" fill="#94a3b8" font-size="11" font-weight="bold">#</text>
    <text x="{pan_x + 65}" y="{tab_y + 20}" fill="#94a3b8" font-size="11" font-weight="bold">COR CABO</text>
    <text x="{pan_x + 195}" y="{tab_y + 20}" fill="#94a3b8" font-size="11" font-weight="bold">PINO RFID</text>
    <text x="{pan_x + 315}" y="{tab_y + 20}" fill="#94a3b8" font-size="11" font-weight="bold">PINO PICO</text>
    <text x="{pan_x + 440}" y="{tab_y + 20}" fill="#94a3b8" font-size="11" font-weight="bold">FUNÇÃO SPI</text>
    ''')

    table_rows = [
        ("1", "#ef4444", "🔴 Vermelho", "3.3V (VCC)", "Pino 36 (3V3 OUT)", "Alimentação 3.3V"),
        ("2", "#94a3b8", "⚫ Preto",    "GND",        "Pino 38 (GND)",     "Terra comum"),
        ("3", "#f1f5f9", "⚪ Branco",   "RST",        "Pino 29 (GP22)",    "Reset do módulo"),
        ("4", "#c084fc", "🟣 Roxo",     "MOSI",       "Pino 25 (GP19)",    "SPI0 TX (Master Out)"),
        ("5", "#60a5fa", "🔵 Azul",     "SCK",        "Pino 24 (GP18)",    "SPI0 SCK (Clock)"),
        ("6", "#4ade80", "🟢 Verde",    "SDA (CS)",   "Pino 22 (GP17)",    "SPI0 CSn (Chip Select)"),
        ("7", "#facc15", "🟡 Amarelo",  "MISO",       "Pino 21 (GP16)",    "SPI0 RX (Master In)"),
        ("8", "#64748b", "⚪ Cinza",    "IRQ (opc.)", "Pino 19 (GP14)",    "Interrupção HW (opc.)")
    ]

    row_y = tab_y + 40
    for num, color, cor_txt, rfid_pin, pico_pin, spi_func in table_rows:
        is_even = int(num) % 2 == 0
        bg_fill = "#1e293b" if is_even else "#0f172a"
        svg.append(f'''
        <rect x="{pan_x + 16}" y="{row_y}" width="{pan_w - 32}" height="32" rx="4" fill="{bg_fill}" opacity="0.8"/>
        <text x="{pan_x + 35}" y="{row_y + 20}" fill="#cbd5e1" font-size="11.5" font-weight="bold">{num}</text>
        <circle cx="{pan_x + 55}" cy="{row_y + 16}" r="5" fill="{color}"/>
        <text x="{pan_x + 68}" y="{row_y + 20}" fill="{color}" font-size="11.5" font-weight="600">{cor_txt}</text>
        <text x="{pan_x + 195}" y="{row_y + 20}" fill="#ffffff" font-size="11.5" font-weight="bold">{rfid_pin}</text>
        <text x="{pan_x + 315}" y="{row_y + 20}" fill="#38bdf8" font-size="11.5" font-weight="bold">{pico_pin}</text>
        <text x="{pan_x + 440}" y="{row_y + 20}" fill="#cbd5e1" font-size="10.5">{spi_func}</text>
        ''')
        row_y += 36

    # CAIXA 1: REGRA DE OURO
    box1_y = row_y + 20
    svg.append(f'''
    <rect x="{pan_x + 16}" y="{box1_y}" width="{pan_w - 32}" height="140" rx="10" fill="#450a0a" stroke="#ef4444" stroke-width="2"/>
    <text x="{pan_x + pan_w/2}" y="{box1_y + 27}" fill="#fca5a5" font-size="13.5" font-weight="800" text-anchor="middle">⚠️ REGRA DE OURO: ALIMENTAÇÃO E TENSÃO</text>
    <line x1="{pan_x + 30}" y1="{box1_y + 38}" x2="{pan_x + pan_w - 30}" y2="{box1_y + 38}" stroke="#7f1d1d" stroke-width="1"/>
    
    <text x="{pan_x + 35}" y="{box1_y + 60}" fill="#fef2f2" font-size="12" font-weight="600">✓ O leitor RFID MFRC522 opera ESTRITAMENTE a 3.3V.</text>
    <text x="{pan_x + 35}" y="{box1_y + 82}" fill="#fef2f2" font-size="12" font-weight="600">✓ Ligue SEMPRE no Pino 36 do Pico (3V3 OUT).</text>
    <text x="{pan_x + 35}" y="{box1_y + 104}" fill="#f87171" font-size="12" font-weight="bold">✗ NUNCA conecte ao Pino 40 (VBUS / 5V) — QUEIMA O LEITOR!</text>
    <text x="{pan_x + 35}" y="{box1_y + 125}" fill="#fca5a5" font-size="11">Os pinos do Pico NÃO toleram 5V. Mantenha toda a ligação a 3.3V.</text>
    ''')

    # CAIXA 2: ESCLARECIMENTO GP15 vs GP17
    box2_y = box1_y + 155
    svg.append(f'''
    <rect x="{pan_x + 16}" y="{box2_y}" width="{pan_w - 32}" height="150" rx="10" fill="#0f172a" stroke="#38bdf8" stroke-width="1.8"/>
    <text x="{pan_x + pan_w/2}" y="{box2_y + 27}" fill="#38bdf8" font-size="13.5" font-weight="800" text-anchor="middle">💡 ESCLARECIMENTO TÉCNICO: GP15 vs GP17</text>
    <line x1="{pan_x + 30}" y1="{box2_y + 38}" x2="{pan_x + pan_w - 30}" y2="{box2_y + 38}" stroke="#1e293b" stroke-width="1"/>

    <text x="{pan_x + 35}" y="{box2_y + 60}" fill="#e2e8f0" font-size="11.5">• <tspan fill="#38bdf8" font-weight="bold">SDA (CS) vai no Pino 22 (GP17):</tspan> Este é o pino nativo SPI0 CSn do RP2040.</text>
    <text x="{pan_x + 35}" y="{box2_y + 80}" fill="#e2e8f0" font-size="11.5">• <tspan fill="#f97316" font-weight="bold">Pino 20 (GP15) é o RELÉ DA PORTA:</tspan> Conforme definido em main.py</text>
    <text x="{pan_x + 50}" y="{box2_y + 98}" fill="#fdba74" font-size="11">(PIN_RELE = 15). Se ligar o RFID no GP15, a trava não funcionará!</text>
    <text x="{pan_x + 35}" y="{box2_y + 118}" fill="#e2e8f0" font-size="11.5">• <tspan fill="#4ade80" font-weight="bold">RST vai no Pino 29 (GP22):</tspan> Fica no lado direito, logo acima do GND.</text>
    <text x="{pan_x + 35}" y="{box2_y + 138}" fill="#a7f3d0" font-size="11">Dessa forma, todos os 7 cabos do RFID conectam-se no LADO DIREITO do Pico!</text>
    ''')

    # CAIXA 3: DICA DOS JUMPERS
    box3_y = box2_y + 165
    svg.append(f'''
    <rect x="{pan_x + 16}" y="{box3_y}" width="{pan_w - 32}" height="110" rx="10" fill="#1e293b" stroke="#64748b" stroke-width="1.5"/>
    <text x="{pan_x + pan_w/2}" y="{box3_y + 25}" fill="#f1f5f9" font-size="13" font-weight="bold" text-anchor="middle">🔌 GUIA DOS JUMPERS (FÊMEA-MACHO)</text>
    <line x1="{pan_x + 30}" y1="{box3_y + 36}" x2="{pan_x + pan_w - 30}" y2="{box3_y + 36}" stroke="#334155" stroke-width="1"/>

    <text x="{pan_x + 35}" y="{box3_y + 57}" fill="#cbd5e1" font-size="11.5">• <tspan fill="#ffffff" font-weight="bold">Ponta FÊMEA (furinho):</tspan> Encaixa nos pinos salientes da barra do RFID-RC522.</text>
    <text x="{pan_x + 35}" y="{box3_y + 77}" fill="#cbd5e1" font-size="11.5">• <tspan fill="#ffffff" font-weight="bold">Ponta MACHO (agulha):</tspan> Espeta nos furos metalizados da placa do Pico.</text>
    <text x="{pan_x + 35}" y="{box3_y + 97}" fill="#a5b4fc" font-size="11">• Não é necessária protoboard ou solda adicional se o Pico já tiver pinos soldados.</text>
    ''')

    # RODAPÉ
    svg.append('''
    <rect x="0" y="1055" width="100%" height="45" fill="#0f172a" stroke="#1e293b" stroke-width="1"/>
    <text x="900" y="1082" fill="#64748b" font-size="12" text-anchor="middle">Projeto Porta-LAOB • Sistema Completo de Controle de Acesso • github.com/VituColombo0/Porta-LAOB</text>
    ''')

    svg.append('</svg>')
    return '\n'.join(svg)

if __name__ == '__main__':
    svg_content = generate_svg()
    out_svg = '/home/lirool/.gemini/antigravity-ide/scratch/Porta-LAOB/docs/images/diagrama_conexao_preciso.svg'
    with open(out_svg, 'w', encoding='utf-8') as f:
        f.write(svg_content)
    print(f'SVG atualizado com sucesso em: {out_svg}')
