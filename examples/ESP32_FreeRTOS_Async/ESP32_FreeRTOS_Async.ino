/**
 * Porta-LAOB - Exemplo Assíncrono para ESP32 com FreeRTOS
 * 
 * Em sistemas de controle de acesso (como a Porta do LAOB), o ESP32 frequentemente
 * precisa gerenciar Wi-Fi, MQTT, logs em servidor, display OLED e relé da fechadura.
 * 
 * Com FreeRTOS, o RFID roda em uma Task dedicada no Core 1, sem bloquear o sistema
 * e enviando eventos via Queue para a Task de controle da porta.
 * 
 * Pinagem padrão no ESP32:
 *   RC522          ESP32
 *   -----------------------
 *   SDA (SS)  -->  GPIO 5
 *   SCK       -->  GPIO 18
 *   MOSI      -->  GPIO 23
 *   MISO      -->  GPIO 19
 *   IRQ       -->  GPIO 4  (ou qualquer pino capaz de interrupção)
 *   GND       -->  GND
 *   RST       -->  GPIO 22
 *   3.3V      -->  3V3
 */

#if defined(ESP32)

#include <Arduino.h>
#include <SPI.h>
#include "RC522_Interrupt.h"

#define PIN_SS   5
#define PIN_RST  22
#define PIN_IRQ  4
#define PIN_RELE 2 // Exemplo: GPIO 2 acionando relé da trava da porta

RC522_Interrupt rfid(PIN_SS, PIN_RST, PIN_IRQ);
QueueHandle_t rfidEventQueue;

// Estrutura enviada pela fila
struct RfidEvent {
    char uid[32];
};

// Callback do leitor
void onCardRead(const String &uidStr, const byte *uidBytes, byte uidSize) {
    RfidEvent event;
    strncpy(event.uid, uidStr.c_str(), sizeof(event.uid));
    xQueueSend(rfidEventQueue, &event, 0);
}

// Task dedicada para a leitura do leitor RFID
void rfidTask(void *pvParameters) {
    SPI.begin(18, 19, 23, 5); // SCK, MISO, MOSI, SS
    rfid.onCardDetected(onCardRead);

    if (!rfid.begin(true)) {
        Serial.println("[Task RFID] Falha ao inicializar MFRC522!");
    } else {
        Serial.println("[Task RFID] Leitor iniciado com sucesso!");
    }

    for (;;) {
        rfid.update();
        vTaskDelay(pdMS_TO_TICKS(20)); // Cede tempo para o RTOS sem sobrecarregar a CPU
    }
}

// Task que gerencia a lógica de abertura da porta
void doorControlTask(void *pvParameters) {
    pinMode(PIN_RELE, OUTPUT);
    digitalWrite(PIN_RELE, LOW);

    RfidEvent receivedEvent;

    for (;;) {
        // Aguarda receber evento da fila
        if (xQueueReceive(rfidEventQueue, &receivedEvent, portMAX_DELAY) == pdTRUE) {
            Serial.printf("[Porta-LAOB] Validando acesso para UID: %s\n", receivedEvent.uid);

            // Exemplo de lógica de validação:
            // if (isAuthorized(receivedEvent.uid)) ...
            Serial.println("[Porta-LAOB] ACESSO LIBERADO! Abrindo trava...");
            digitalWrite(PIN_RELE, HIGH);
            vTaskDelay(pdMS_TO_TICKS(3000)); // Mantém aberta por 3 segundos
            digitalWrite(PIN_RELE, LOW);
            Serial.println("[Porta-LAOB] Porta fechada e travada novamente.");
        }
    }
}

void setup() {
    Serial.begin(115200);
    delay(1000);
    Serial.println("========================================");
    Serial.println("  Iniciando Sistema Porta-LAOB (ESP32)  ");
    Serial.println("========================================");

    rfidEventQueue = xQueueCreate(5, sizeof(RfidEvent));

    // Cria as tasks fixando-as nos núcleos do ESP32
    xTaskCreatePinnedToCore(rfidTask, "RFID_Task", 4096, NULL, 2, NULL, 1);
    xTaskCreatePinnedToCore(doorControlTask, "Door_Task", 4096, NULL, 1, NULL, 0);
}

void loop() {
    // Loop vazio, todo o sistema opera via FreeRTOS
    vTaskDelay(pdMS_TO_TICKS(1000));
}

#endif
