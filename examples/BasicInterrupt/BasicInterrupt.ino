/**
 * Porta-LAOB - Exemplo Básico com Interrupção por Hardware
 * 
 * Este exemplo demonstra o uso da classe RC522_Interrupt eliminando os bugs
 * do exemplo original 'MinimalInterrupt' (como congelamento no setup e polling travado).
 * 
 * Pinagem típica (Arduino Uno / Nano):
 *   RC522          Arduino
 *   -----------------------
 *   SDA (SS)  -->  D10
 *   SCK       -->  D13
 *   MOSI      -->  D11
 *   MISO      -->  D12
 *   IRQ       -->  D2  (Pino de interrupção externa)
 *   GND       -->  GND
 *   RST       -->  D9
 *   3.3V      -->  3.3V (NUNCA ligue no 5V!)
 */

#include <SPI.h>
#include "RC522_Interrupt.h"

#define SS_PIN  10
#define RST_PIN 9
#define IRQ_PIN 2

RC522_Interrupt rfid(SS_PIN, RST_PIN, IRQ_PIN);

// Callback executado imediatamente quando uma tag é lida
void quandoCartaoDetectado(const String &uidStr, const byte *uidBytes, byte uidSize) {
    Serial.println();
    Serial.println(F("========================================"));
    Serial.print(F(">>> CARTÃO DETECTADO VIA INTERRUPÇÃO! UID: "));
    Serial.println(uidStr);
    Serial.print(F("Tamanho do UID: "));
    Serial.print(uidSize);
    Serial.println(F(" bytes"));
    Serial.println(F("========================================"));
    
    // Aqui você pode acionar a trava da porta, buzzer, LED, etc.
}

void setup() {
    Serial.begin(115200);
    while (!Serial);

    Serial.println(F("--- Porta-LAOB: Iniciando Sistema RFID com Interrupção ---"));
    SPI.begin();

    // Registra o callback de evento
    rfid.onCardDetected(quandoCartaoDetectado);

    // Inicializa o leitor e os registradores de interrupção
    // true = modo Push-Pull (padrão)
    if (!rfid.begin(true)) {
        Serial.println(F("[ERRO] Falha ao comunicar com o MFRC522. Verifique conexões e 3.3V!"));
        while (true) delay(1000);
    }

    Serial.println(F("[OK] MFRC522 pronto e aguardando cartões por interrupção..."));
}

void loop() {
    // Atualiza a máquina de estados da interrupção (não-bloqueante)
    rfid.update();

    // O loop() continua rodando livremente para outras tarefas!
    // Exemplo: piscar LED, verificar botões, sensores de abertura de porta, etc.
}
