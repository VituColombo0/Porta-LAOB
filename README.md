# Porta-LAOB 🚪🔑

Sistema de controle de acesso para porta do laboratório LAOB utilizando leitor RFID-RC522, acionamento eletrônico de fechadura e suporte nativo ao **Raspberry Pi Pico (RP2040)**.

---

## 🎯 Missão 1: Tratamento do RFID-RC522 e o Desafio da Interrupção (IRQ)

### O Problema Encontrado
A biblioteca padrão para o leitor RC522 (`miguelbalboa/rfid`) inclui um exemplo chamado `MinimalInterrupt.ino`, porém **ele não funciona na prática** para a maioria dos desenvolvedores. Os sintomas comuns são:
1. **Travamento no boot:** O código congela dentro do `setup()` devido ao laço bloqueante `do { } while (!bNewInt);`.
2. **Leitura única:** Após ler o primeiro cartão, a linha IRQ não desarma corretamente e o leitor para de responder.
3. **Mito do "Wake-on-Card":** O chip MFRC522 **não possui hardware de detecção autônoma de presença de cartão (LPCD)** como o PN532. Ele não acorda um microcontrolador em Deep Sleep por aproximação sem que o transmissor esteja emitindo o comando `REQA`.

### A Solução Implementada no Porta-LAOB
Desenvolvemos soluções modulares e robustas para **Raspberry Pi Pico**:
* **MicroPython com IRQ por Hardware:** [`micropython/rc522_irq.py`](micropython/rc522_irq.py) e [`micropython/main_irq.py`](micropython/main_irq.py).
* **MicroPython Dual-Core (RP2040):** [`micropython/main_multicore.py`](micropython/main_multicore.py) aproveitando os 2 núcleos do RP2040 (Core 1 para RFID em tempo real e Core 0 para a porta).
* **Driver C++ Multiplataforma:** [`include/RC522_Interrupt.h`](include/RC522_Interrupt.h) e [`src/RC522_Interrupt.cpp`](src/RC522_Interrupt.cpp) com exemplos em [`examples/`](examples/).

---

## 📁 Estrutura do Repositório

```text
Porta-LAOB/
├── micropython/
│   ├── mfrc522.py                         # Driver base MFRC522 para Raspberry Pi Pico
│   ├── rc522_irq.py                       # Driver com interrupção por hardware (IRQ)
│   ├── main_irq.py                        # Exemplo de controle de porta via IRQ
│   └── main_multicore.py                  # Exemplo assíncrono via DUAL-CORE (RP2040)
├── docs/
│   └── analise_interrupcao_rc522.md       # Estudo aprofundado dos registradores e bugs
├── include/
│   └── RC522_Interrupt.h                 # Driver C++ para Arduino/Pico SDK
├── src/
│   └── RC522_Interrupt.cpp               # Implementação C++ com controle de registradores
├── examples/
│   ├── BasicInterrupt/
│   │   └── BasicInterrupt.ino             # Exemplo básico de interrupção
│   └── ESP32_FreeRTOS_Async/
│       └── ESP32_FreeRTOS_Async.ino       # Arquitetura com FreeRTOS
└── README.md
```

---

## 🔌 Pinagem e Conexões no Raspberry Pi Pico

> 💡 **Vantagem do Raspberry Pi Pico:** Opera nativamente em **3.3V**, garantindo 100% de compatibilidade elétrica e segurança para o leitor RC522 sem necessidade de conversores de nível lógico.

| Pino MFRC522 | Raspberry Pi Pico (Pino Físico) | Função no Pico |
| :--- | :--- | :--- |
| **3.3V (VCC)** | **3V3 OUT (Pino 36)** | Alimentação 3.3V regulada |
| **GND** | **GND (Pino 38)** | Terra comum |
| **RST** | **GP22 (Pino 29)** | Reset do leitor |
| **IRQ** | **GP14 (Pino 19)** | Interrupção externa de Hardware |
| **MISO** | **GP16 (Pino 21)** | SPI0 RX |
| **MOSI** | **GP19 (Pino 25)** | SPI0 TX |
| **SCK** | **GP18 (Pino 24)** | SPI0 SCK |
| **SDA (CS)** | **GP17 (Pino 22)** | SPI0 CSn (Chip Select) |
| --- | --- | --- |
| **RELÉ (Trava)** | **GP15 (Pino 20)** | Saída digital para acionar relé |

---

## 🚀 Como Executar no Raspberry Pi Pico

### Opção 1: Usando MicroPython com Interrupção por Hardware (IRQ)
1. Copie os arquivos [`micropython/mfrc522.py`](micropython/mfrc522.py), [`micropython/rc522_irq.py`](micropython/rc522_irq.py) e [`micropython/main_irq.py`](micropython/main_irq.py) para o Raspberry Pi Pico (usando Thonny, VS Code ou mpremote).
2. Execute o `main_irq.py`. O leitor responderá via interrupção sem laços de delay bloqueantes.

### Opção 2: Usando MicroPython com DUAL-CORE (RP2040)
1. O RP2040 possui 2 núcleos de processamento independentes.
2. Com [`micropython/main_multicore.py`](micropython/main_multicore.py), o **Core 1** faz a varredura contínua do RFID sem ocupar nem 1% do tempo do **Core 0**, enquanto o **Core 0** cuida das travas, botões e telas.

---

## 📖 Leitura Recomendada
Para entender no detalhe os registradores internos (`ComIEnReg`, `DivIEnReg`, `ComIrqReg`, etc.) e por que o exemplo original falhava, consulte o documento [**Análise Técnica da Interrupção no RC522**](docs/analise_interrupcao_rc522.md).
