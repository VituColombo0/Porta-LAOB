"""
Porta-LAOB - Modo Interrupção por Hardware (IRQ)
Plataforma: Raspberry Pi Pico (MicroPython)
Arquivo: main_irq.py (Modo alternativo usando pino IRQ)

Este script usa o pino GP14 para receber a interrupção física de borda de descida
do leitor RC522 quando uma tag é aproximada, sem uso de laços bloqueantes.
"""

from machine import Pin, SPI
import time
from rc522_irq import RC522_Pico_IRQ
from door_manager import DoorManager

# Definições de Pinos
PIN_SCK    = 18
PIN_MOSI   = 19
PIN_MISO   = 16
PIN_CS     = 17
PIN_RST    = 22
PIN_IRQ    = 14
PIN_RELE   = 15
PIN_BOTAO  = 13
PIN_BUZZER = 12
PIN_SENSOR = 11

door = DoorManager(relay_pin=PIN_RELE,
                   button_pin=PIN_BOTAO,
                   buzzer_pin=PIN_BUZZER,
                   sensor_pin=PIN_SENSOR,
                   relay_active_high=True)

def quando_tag_detectada(uid_str, uid_bytes):
    door.process_uid(uid_str)

def main():
    print("==================================================")
    print("   Porta-LAOB - Modo Interrupção por Hardware     ")
    print("==================================================")

    spi = SPI(0, baudrate=1_000_000, polarity=0, phase=0,
              sck=Pin(PIN_SCK), mosi=Pin(PIN_MOSI), miso=Pin(PIN_MISO))

    rfid = RC522_Pico_IRQ(spi, cs_pin=PIN_CS, rst_pin=PIN_RST, irq_pin=PIN_IRQ, push_pull=True)
    rfid.on_card(quando_tag_detectada)

    print(f"[OK] Leitor configurado no pino IRQ GP{PIN_IRQ}. Aguardando crachás...")

    while True:
        # Atualiza a máquina de estados não-bloqueante
        rfid.update()

        # Verifica botoeira e sensor de porta
        door.check_inputs()

        time.sleep_ms(20)

if __name__ == "__main__":
    main()
