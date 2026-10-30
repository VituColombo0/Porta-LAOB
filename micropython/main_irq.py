"""
Porta-LAOB - Controle de Acesso com Interrupção por Hardware (IRQ)
Plataforma: Raspberry Pi Pico (MicroPython)

Pinagem Recomendada no Pico:
  MFRC522      Raspberry Pi Pico
  -------------------------------
  VCC (3.3V)-> 3V3 OUT (Pino 36)
  GND       -> GND (Pino 38)
  RST       -> GP22 (Pino 29)
  IRQ       -> GP14 (Pino 19) [Interrupção Externa]
  MISO (RX) -> GP16 (Pino 21) [SPI0 RX]
  MOSI (TX) -> GP19 (Pino 25) [SPI0 TX]
  SCK       -> GP18 (Pino 24) [SPI0 SCK]
  SDA (CS)  -> GP17 (Pino 22) [SPI0 CS]
  -------------------------------
  RELÉ      -> GP15 (Pino 20) [Trava da Porta]
  BUZZER    -> GP13 (Pino 17) [Opcional]
"""

from machine import Pin, SPI
import time
from rc522_irq import RC522_Pico_IRQ

# Configuração dos Pinos
PIN_SCK  = 18
PIN_MOSI = 19
PIN_MISO = 16
PIN_CS   = 17
PIN_RST  = 22
PIN_IRQ  = 14
PIN_RELE = 15
PIN_LED  = "LED" # LED onboard do Pico

rele = Pin(PIN_RELE, Pin.OUT)
rele.value(0) # Trava fechada

led_onboard = Pin(PIN_LED, Pin.OUT)

# Lista de UIDs autorizados no LAOB (adicione as tags do seu laboratório aqui)
TAGS_AUTORIZADAS = [
    "A1 B2 C3 D4",
    "43 8A 1F 2C"
]

def abrir_porta():
    print("[PORTA-LAOB] ACESSO LIBERADO! Abrindo trava...")
    led_onboard.value(1)
    rele.value(1) # Aciona relé
    time.sleep(3) # Mantém aberta por 3 segundos
    rele.value(0) # Trava novamente
    led_onboard.value(0)
    print("[PORTA-LAOB] Porta trancada com sucesso.")

def quando_cartao_detectado(uid_str, uid_bytes):
    print("\n-------------------------------------------")
    print(f">> CARTÃO DETECTADO VIA IRQ! UID: {uid_str}")
    
    if uid_str in TAGS_AUTORIZADAS:
        abrir_porta()
    else:
        print("[ACESSO NEGADO] Tag não cadastrada no LAOB.")
        # Pisca LED 3 vezes indicando erro
        for _ in range(3):
            led_onboard.value(1)
            time.sleep_ms(100)
            led_onboard.value(0)
            time.sleep_ms(100)
    print("-------------------------------------------\n")

def main():
    print("Iniciando Porta-LAOB no Raspberry Pi Pico...")
    
    # Inicializa o barramento SPI0 de hardware do RP2040
    spi = SPI(0, baudrate=1_000_000, polarity=0, phase=0,
              sck=Pin(PIN_SCK), mosi=Pin(PIN_MOSI), miso=Pin(PIN_MISO))

    # Inicializa o driver com suporte a IRQ
    rfid = RC522_Pico_IRQ(spi, cs_pin=PIN_CS, rst_pin=PIN_RST, irq_pin=PIN_IRQ, push_pull=True)
    rfid.on_card(quando_cartao_detectado)

    print("Leitor RFID pronto e operando por interrupção. Aproxime a tag...")

    while True:
        # Atualiza a máquina de estados (não-bloqueante)
        rfid.update()

        # O loop principal fica livre para executar outras rotinas
        # (ex: checar botão de saída da sala, sensor de porta aberta, etc.)
        time.sleep_ms(20)

if __name__ == "__main__":
    main()
