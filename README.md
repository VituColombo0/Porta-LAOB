# Porta-LAOB 🚪🔑

Sistema de controle de acesso para porta do laboratório LAOB utilizando leitor RFID-RC522 e acionamento eletrônico de fechadura.

---

## 🎯 Missão 1: Tratamento do RFID-RC522 e o Desafio da Interrupção (IRQ)

### O Problema Encontrado
A biblioteca padrão para o leitor RC522 (`miguelbalboa/rfid`) inclui um exemplo chamado `MinimalInterrupt.ino`, porém **ele não funciona na prática** para a maioria dos desenvolvedores. Os sintomas comuns são:
1. **Travamento no boot:** O código congela dentro do `setup()` devido ao laço bloqueante `do { } while (!bNewInt);`.
2. **Leitura única:** Após ler o primeiro cartão, a linha IRQ não desarma corretamente e o leitor para de responder.
3. **Mito do "Wake-on-Card":** O chip MFRC522 **não possui hardware de detecção autônoma de presença de cartão (LPCD)** como o PN532. Ele não acorda um microcontrolador em Deep Sleep por aproximação sem que o transmissor esteja emitindo o comando `REQA`.

### A Solução Implementada no Porta-LAOB
Desenvolvemos o módulo C++ **`RC522_Interrupt`** ([`include/RC522_Interrupt.h`](include/RC522_Interrupt.h) e [`src/RC522_Interrupt.cpp`](src/RC522_Interrupt.cpp)), que:
* Configura diretamente os registradores de interrupção do MFRC522 (`DivIEnReg` e `ComIEnReg`).
* Corrige o modo de saída do pino IRQ (Push-Pull vs Open-Drain).
* Elimina completamente o travamento de inicialização.
* Gerencia o ciclo de vida completo da leitura (`Read -> Halt -> StopCrypto -> ClearFlags -> Re-arm`).
* Oferece arquitetura orientada a eventos (`onCardDetected(callback)`).
* Oferece suporte completo para **FreeRTOS assíncrono no ESP32** com tarefas desacopladas e filas de eventos (`QueueHandle_t`).

---

## 📁 Estrutura do Repositório

```text
Porta-LAOB/
├── docs/
│   └── analise_interrupcao_rc522.md       # Estudo aprofundado dos registradores e bugs
├── include/
│   └── RC522_Interrupt.h                 # Declaração da classe e tipos de callback
├── src/
│   └── RC522_Interrupt.cpp               # Implementação do driver com controle de registradores
├── examples/
│   ├── BasicInterrupt/
│   │   └── BasicInterrupt.ino             # Exemplo básico de interrupção para Arduino Uno/Nano
│   └── ESP32_FreeRTOS_Async/
│       └── ESP32_FreeRTOS_Async.ino       # Arquitetura profissional assíncrona para ESP32
└── README.md
```

---

## 🔌 Pinagem e Conexões

> ⚠️ **ATENÇÃO:** O módulo RC522 opera estritamente com **3.3V**. Nunca conecte o pino VCC aos 5V do Arduino!

### Conexão no Arduino (Uno / Nano / Pro Mini)
| MFRC522 | Arduino Uno / Nano | Descrição |
| :--- | :--- | :--- |
| **3.3V** | 3.3V | Alimentação estrita 3.3V |
| **GND** | GND | Terra comum |
| **RST** | D9 | Reset do leitor |
| **IRQ** | **D2** | Pino de Interrupção Externa (INT0) |
| **MISO** | D12 | SPI MISO |
| **MOSI** | D11 | SPI MOSI |
| **SCK** | D13 | SPI Clock |
| **SDA (SS)** | D10 | SPI Slave Select |

### Conexão no ESP32
| MFRC522 | ESP32 | Descrição |
| :--- | :--- | :--- |
| **3.3V** | 3V3 | Alimentação 3.3V |
| **GND** | GND | Terra comum |
| **RST** | GPIO 22 | Reset do leitor |
| **IRQ** | **GPIO 4** | Pino de Interrupção de Hardware |
| **MISO** | GPIO 19 | SPI MISO (VSPI) |
| **MOSI** | GPIO 23 | SPI MOSI (VSPI) |
| **SCK** | GPIO 18 | SPI Clock (VSPI) |
| **SDA (SS)** | GPIO 5 | SPI Slave Select (VSPI) |

---

## 🚀 Como Usar no seu Código

### Exemplo Rápido (Arduino)
```cpp
#include <SPI.h>
#include "RC522_Interrupt.h"

RC522_Interrupt rfid(10, 9, 2); // SS, RST, IRQ

void setup() {
    Serial.begin(115200);
    SPI.begin();

    rfid.onCardDetected([](const String &uid, const byte *bytes, byte size) {
        Serial.print("Tag lida: ");
        Serial.println(uid);
    });

    rfid.begin(true); // true = modo Push-Pull
}

void loop() {
    rfid.update(); // Não-bloqueante
}
```

---

## 📖 Leitura Recomendada
Para entender no detalhe os registradores internos (`ComIEnReg`, `DivIEnReg`, `ComIrqReg`, etc.) e por que o exemplo original falhava, consulte o documento [**Análise Técnica da Interrupção no RC522**](docs/analise_interrupcao_rc522.md).
