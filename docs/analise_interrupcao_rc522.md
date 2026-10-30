# Análise Técnica Profunda: O Problema da Interrupção (IRQ) no RFID-RC522

## 1. O Problema Relatado
Ao tentar utilizar a biblioteca padrão `miguelbalboa/rfid` (ou derivadas) com o pino de interrupção (`IRQ`), muitos desenvolvedores se deparam com os seguintes problemas:
1. O microcontrolador **trava no `setup()`** e nunca entra no `loop()`.
2. A leitura funciona apenas **uma única vez** e depois o pino IRQ nunca mais dispara.
3. Há a impressão de que a interrupção deveria "acordar o leitor ou microcontrolador quando um cartão se aproxima", mas nada acontece a menos que haja um loop ativo.

---

## 2. Por que o exemplo `MinimalInterrupt.ino` falha na prática?

O exemplo oficial disponibilizado na biblioteca de Miguel Balboa contém falhas de arquitetura e bugs de código:

### Bug A: O laço de travamento no `setup()`
No código original do exemplo:
```cpp
attachInterrupt(digitalPinToInterrupt(IRQ_PIN), readCard, FALLING);
do { //clear a spurious interrupt at start
  ;
} while (!bNewInt);
bNewInt = false;
```
**O que acontece:** O autor colocou um `do { } while (!bNewInt);` na esperança de "capturar um glitch elétrico inicial". Contudo, se a linha IRQ estiver estável e não houver ruído, `bNewInt` continuará `false`, e a placa **congela indefinidamente no boot**.

### Bug B: Passagem de objeto por valor (Copy por engano em C++)
No exemplo:
```cpp
void activateRec(MFRC522 mfrc522);
```
O objeto `MFRC522` é passado **por valor** (copiado para a pilha) a cada chamada em vez de passar por referência (`&mfrc522`). Isso gera cópias de estado e overhead inútil.

### Bug C: A falsa interrupção ("Polling disfarçado")
No `loop()` do exemplo:
```cpp
activateRec(mfrc522);
delay(100);
```
Mesmo com o pino IRQ conectado, o código continua executando `delay(100)` e polling manual.

### Bug D: Travamento da linha IRQ após a 1ª leitura
Para que uma nova interrupção ocorra, os registradores `ComIrqReg` (0x04) e `DivIrqReg` (0x05) precisam ter suas flags limpas (escrevendo `0x7F`). Se isso não for feito em conjunto com o encerramento da sessão da tag (`PICC_HaltA()` e `PCD_StopCrypto1()`), a saída de interrupção do MFRC522 permanece ativada em nível baixo (LOW) e nenhuma nova borda de descida (`FALLING`) é detectada pelo microcontrolador.

---

## 3. Limitação Fisiológica do Hardware NXP MFRC522

Existe uma confusão comum entre **Detecção de Proximidade** e **Interrupção de Comunicação**:
* **Cartões RFID passivos não emitem sinal no ar por conta própria.** Eles dependem da energia eletromagnética irradiada pela antena do leitor.
* O MFRC522 **NÃO possui LPCD (Low-Power Card Detection)** autônomo (presente em chips mais caros como NXP CLRC663 ou PN532).
* O pino IRQ do MFRC522 só avisa quando um evento de comando terminou (ex: dados recebidos no FIFO com `RxIRq` ou término de transmissão `TxIRq`).
* Portanto, **o transmissor precisa emitir o comando `REQA` periodicamente** para que, se houver um cartão na frente, a resposta dele acione o `RxIRq` e puxe o pino físico para LOW.

---

## 4. O Registrador `DivIEnReg` e o pino IRQ (Open-Drain vs Push-Pull)
No datasheet do NXP MFRC522 (Seção 8.1.11 / Tabela 25):
* **Registrador `DivIEnReg` (endereço `0x03`), Bit 7 (`IRQPushPull`)**:
  * Se `Bit 7 = 0`: O pino IRQ opera em **Open-Drain** (dreno aberto). Requer resistor de pull-up (interno no MCU ou externo) e trigger `FALLING`.
  * Se `Bit 7 = 1`: O pino IRQ opera em **Push-Pull** (nível lógico ativo padrão CMOS).

---

## 5. Como o módulo `RC522_Interrupt` do Porta-LAOB resolveu o problema
Criamos o driver encapsulado [`RC522_Interrupt`](../include/RC522_Interrupt.h):
1. **Eliminou o travamento de boot:** Removeu o laço bloqueante e realizou a purga de transientes com limpeza direta nos registradores.
2. **Configuração Explícita de Registradores:** Permite alternar entre Push-Pull e Open-Drain e habilita `RxIEn` e `IdleIEn` em `ComIEnReg (0xA0)`.
3. **Encapsulamento C++ Orientado a Eventos:** O desenvolvedor define `onCardDetected([](String uid, ...))` e executa `rfid.update()` de maneira não-bloqueante.
4. **Re-armação e Limpeza Automática:** Após a leitura de um UID, o driver desativa a tag (`HaltA`), para o cripto e limpa as flags para deixar o módulo instantaneamente pronto para o próximo crachá.
5. **Compatibilidade ESP32 FreeRTOS:** Permite rodar o leitor em uma Task dedicada com filas de mensagens, ideal para a fechadura do laboratório LAOB.
