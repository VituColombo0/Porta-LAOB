# Porta-LAOB

Sistema embarcado de controle de acesso para portas de laboratório utilizando microcontrolador Raspberry Pi Pico (RP2040), leitor RFID MFRC522 e acionamento eletrônico de fechadura via relé.

[![Platform: RP2040](https://img.shields.io/badge/Platform-RP2040%20%7C%20Pico-blue.svg)](https://www.raspberrypi.com/products/raspberry-pi-pico/)
[![Firmware: MicroPython](https://img.shields.io/badge/Firmware-MicroPython-informational.svg)](https://micropython.org/)
[![C++ SDK](https://img.shields.io/badge/Driver-C%2B%2B%20%2F%20Arduino-darkgreen.svg)](https://github.com/VituColombo0/Porta-LAOB)
[![Simulator: Wokwi](https://img.shields.io/badge/Simulation-Wokwi%202D-orange.svg)](wokwi.toml)

---

## Documentação Técnica

- [Diagrama Detalhado de Montagem e Conectores Macho/Fêmea](docs/DIAGRAMA_MONTAGEM.md)
- [Tutorial Passo a Passo de Instalação e Configuração](TUTORIAL_PASSO_A_PASSO.md)
- [Estudo Técnico dos Registradores e Análise de IRQ no RC522](docs/analise_interrupcao_rc522.md)
- [Simulação Interativa Wokwi](wokwi.toml)

---

## Arquitetura e Engenharia do Sistema

O projeto resolve desafios críticos de confiabilidade frequentemente encontrados no uso do leitor MFRC522 com microcontroladores de baixo custo:

```
┌─────────────────────────────────────────────────────────────┐
│                 Raspberry Pi Pico (RP2040)                  │
├──────────────────────────────┬──────────────────────────────┤
│            Core 0            │            Core 1            │
│  - Gestão de fechadura       │  - Varredura contínua SPI    │
│  - Botoeira interna (GP13)   │  - Leitura rápida de UID     │
│  - Sensor de porta (GP11)    │  - Decodificação 4/7 bytes   │
│  - Feedback sonoro (GP12)    │  - Fila thread-safe de tags  │
│  - Persistência em JSON      │                              │
└──────────────┬───────────────┴──────────────┬───────────────┘
               │                              │
               ▼                              ▼
      [ Relé / Fechadura ]            [ MFRC522 Leitor ]
```

### Análise da Linha IRQ e Limitações do MFRC522

O exemplo clássico `MinimalInterrupt.ino` distribuído na biblioteca padrão de Arduino apresenta falhas estruturais em cenários de produção:
1. **Travamento no Boot:** Um laço bloqueante `do { } while (!bNewInt);` no setup interrompe a inicialização caso o registrador de interrupções não inicialize com a linha em nível baixo.
2. **Perda de Re-armação:** Após a primeira leitura de cartão, as flags de interrupção (`ComIrqReg` e `DivIrqReg`) deixam de ser limpas adequadamente em alguns clones do chip, travando leituras subsequentes.
3. **Ausência de LPCD Nativo:** O chip MFRC522 não possui detecção passiva de baixa potência por aproximação (LPCD), diferentemente de controladores como o PN532. Ele requer transmissão ativa de campo magnético (`REQA`/`WUPA`) para detectar o cartão.

### Soluções Implementadas no Porta-LAOB

- **Arquitetura Dual-Core em MicroPython ([`micropython/main.py`](micropython/main.py)):** Isola a rotina de varredura SPI do leitor no **Core 1**, mantendo o **Core 0** 100% responsivo para a botoeira de saída interna, temporização da trava e sinalização sonora, sem travamentos na interface.
- **Tratamento de IRQ em Nível de Hardware ([`micropython/rc522_irq.py`](micropython/rc522_irq.py)):** Controle direto dos registradores `ComIEnReg` e `DivIEnReg`, com re-armação e limpeza atômica das interrupções.
- **Gerenciador de Acesso Autônomo ([`micropython/door_manager.py`](micropython/door_manager.py)):** Armazenamento das tags autorizadas em arquivo JSON na flash interna (`authorized_tags.json`). Inclui modo Administrador (cartão Master para cadastro/exclusão direta na porta sem necessidade de computador) e registro de logs de auditoria.
- **Driver C++ Otimizado ([`include/RC522_Interrupt.h`](include/RC522_Interrupt.h), [`src/RC522_Interrupt.cpp`](src/RC522_Interrupt.cpp)):** Disponível para projetos com Pico C/C++ SDK ou Arduino IDE.

---

## Esquema de Ligação Fio-a-Fio (3.3V)

> **Compatibilidade Elétrica:** O Raspberry Pi Pico opera nativamente em níveis lógicos de 3.3V, garantindo compatibilidade direta com o MFRC522 sem necessidade de shifters de nível bidirecionais.

![Diagrama Preciso de Ligação Direta](docs/images/diagrama_conexao_preciso.png)

| Dispositivo | Pino no Módulo | Pino Físico (Pico) | GPIO RP2040 | Descrição / Função |
| :--- | :--- | :--- | :--- | :--- |
| **MFRC522** | **3.3V (VCC)** | Pino 36 | `3V3 OUT` | Alimentação regulada 3.3V |
| **MFRC522** | **GND** | Pino 38 | `GND` | Terra comum |
| **MFRC522** | **RST** | Pino 29 | `GP22` | Reset de hardware |
| **MFRC522** | **IRQ** | Pino 18 | `GP14` | Interrupção por hardware |
| **MFRC522** | **MISO** | Pino 21 | `GP16` | SPI0 RX |
| **MFRC522** | **MOSI** | Pino 25 | `GP19` | SPI0 TX |
| **MFRC522** | **SCK** | Pino 24 | `GP18` | SPI0 Clock |
| **MFRC522** | **SDA (CS)** | Pino 22 | `GP17` | SPI0 Chip Select |
| **Fechadura** | Sinal Relé | Pino 19 | `GP15` | Acionamento da solenoide/eletroímã |
| **Botoeira** | Saída Interna | Pino 17 | `GP13` | Entrada com Pull-up interno |
| **Buzzer** | Terminal (+) | Pino 16 | `GP12` | Feedback sonoro (PWM/Beep) |
| **Sensor Porta** | Reed Switch | Pino 15 | `GP11` | Monitor de abertura (Opcional) |

---

## Estrutura do Repositório

```text
Porta-LAOB/
├── TUTORIAL_PASSO_A_PASSO.md      # Instruções de montagem mecânica e elétrica
├── micropython/
│   ├── main.py                    # Aplicação Dual-Core principal de boot
│   ├── mfrc522.py                 # Driver SPI MFRC522 otimizado (4 e 7 bytes)
│   ├── rc522_irq.py               # Driver com interrupção por hardware
│   ├── door_manager.py            # Validação de credenciais, logs e modo Master
│   ├── main_irq.py                # Implementação alternativa orientada a IRQ
│   └── main_multicore.py          # Exemplo enxuto de operação multicore
├── tools/
│   └── pico_tool.py               # Utilitário CLI para detecção, upload e monitor serial
├── tests/
│   └── test_door_logic.py         # Testes automatizados da lógica de permissão
├── docs/
│   ├── DIAGRAMA_MONTAGEM.md       # Diagrama fotográfico com guias de crimpagem
│   ├── analise_interrupcao_rc522.md # Investigação aprofundada de hardware
│   └── images/                    # Imagens esquemáticas de pinagem
├── include/
│   └── RC522_Interrupt.h         # Headers C++ para SDK nativo
├── src/
│   └── RC522_Interrupt.cpp       # Implementação em C++
├── examples/
│   ├── BasicInterrupt/            # Exemplo C++ standalone
│   └── ESP32_FreeRTOS_Async/      # Implementação para ESP32 via filas FreeRTOS
├── diagram.json                   # Esquema para simulação no Wokwi
└── wokwi.toml                     # Metadados de ambiente Wokwi
```

---

## Instalação e Uso

### Opção 1: Upload via `pico_tool.py` (Recomendado)

O repositório inclui uma ferramenta CLI em Python para gerenciar o dispositivo sem IDE gráfica:

```bash
# Detectar dispositivo conectado na porta serial
python tools/pico_tool.py list

# Enviar os arquivos do firmware para a raiz do Pico
python tools/pico_tool.py upload micropython/mfrc522.py micropython/door_manager.py micropython/main.py

# Acompanhar a execução em tempo real via terminal serial
python tools/pico_tool.py monitor
```

### Opção 2: Via Thonny IDE

1. Instale o firmware oficial do MicroPython no Raspberry Pi Pico.
2. Abra o **Thonny IDE** e selecione o interpretador `MicroPython (Raspberry Pi Pico)`.
3. Transfira para a raiz (`/`) da placa os arquivos:
   - `micropython/mfrc522.py`
   - `micropython/door_manager.py`
   - `micropython/main.py`
4. Reinicie a alimentação da placa. O script `main.py` inicia automaticamente na inicialização.

### Fluxo de Gerenciamento de Acesso

1. **Primeira Inicialização:** O sistema detecta a ausência de um cartão mestre. Aproxime a tag que será designada como **Administrador (Master)**. O sistema emitirá confirmação sonora e salvará a tag.
2. **Cadastro de Novos Usuários:** Aproxime a tag Master. O sistema entrará no modo de cadastro (sinalizado por bipes intermitentes). Aproxime o novo crachá para registrá-lo.
3. **Exclusão de Usuários:** Aproxime a tag Master duas vezes seguidas para acessar o modo de exclusão e aproxime a tag a ser revogada.

---

## Testes Automatizados

O repositório possui suíte de testes unitários que valida as regras de transição de estado da trava, timeouts de segurança e permissões:

```bash
python -m unittest tests/test_door_logic.py
```

---

## Licença

Desenvolvido para o Laboratório LAOB. Código aberto para fins acadêmicos e laboratoriais.
