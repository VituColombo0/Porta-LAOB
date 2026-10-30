"""
Porta-LAOB - Controle Assíncrono com DUAL-CORE (RP2040)
Plataforma: Raspberry Pi Pico (MicroPython)

O processador RP2040 do Raspberry Pi Pico possui DOIS núcleos ARM Cortex-M0+.
Neste exemplo, aproveitamos esse poder de hardware:
- NÚCLEO 1 (Core 1): Roda a leitura do RFID em segundo plano em tempo real.
- NÚCLEO 0 (Core 0): Roda a fechadura eletrônica, botões e regras de acesso.
"""

from machine import Pin, SPI
import time
import _thread
from mfrc522 import MFRC522

# Pinagem SPI0 do Pico
PIN_SCK  = 18
PIN_MOSI = 19
PIN_MISO = 16
PIN_CS   = 17
PIN_RST  = 22
PIN_RELE = 15
PIN_LED  = "LED"

rele = Pin(PIN_RELE, Pin.OUT)
rele.value(0)
led = Pin(PIN_LED, Pin.OUT)

# Variáveis compartilhadas entre os núcleos protegidas por Lock
lock = _thread.allocate_lock()
tag_encontrada = None

TAGS_AUTORIZADAS = [
    "A1 B2 C3 D4",
    "43 8A 1F 2C"
]

def rfid_core1_worker():
    """Esta função roda EXCLUSIVAMENTE no Core 1 do RP2040"""
    global tag_encontrada

    spi = SPI(0, baudrate=1_000_000, polarity=0, phase=0,
              sck=Pin(PIN_SCK), mosi=Pin(PIN_MOSI), miso=Pin(PIN_MISO))
    rdr = MFRC522(spi, PIN_CS, PIN_RST)
    print("[CORE 1] Scanner RFID rodando em paralelo no Core 1!")

    while True:
        status, _ = rdr.request(rdr.PICC_REQIDL)
        if status == rdr.OK:
            status, uid = rdr.anticoll()
            if status == rdr.OK and len(uid) >= 4:
                uid_str = "{:02X} {:02X} {:02X} {:02X}".format(uid[0], uid[1], uid[2], uid[3])
                
                # Passa a tag lida com segurança para o Core 0
                with lock:
                    tag_encontrada = uid_str
                
                rdr.halt()
                time.sleep_ms(1000) # Evita leituras duplicadas imediatas
        time.sleep_ms(30)

def main():
    global tag_encontrada
    print("Iniciando Porta-LAOB com arquitetura Dual-Core no RP2040...")

    # Dispara o worker no Core 1
    _thread.start_new_thread(rfid_core1_worker, ())

    print("[CORE 0] Sistema de controle de porta pronto no Core 0.")

    while True:
        nova_tag = None
        with lock:
            if tag_encontrada is not None:
                nova_tag = tag_encontrada
                tag_encontrada = None

        if nova_tag:
            print(f"\n[CORE 0] Processando tag: {nova_tag}")
            if nova_tag in TAGS_AUTORIZADAS:
                print("[CORE 0] ACESSO LIBERADO! Destrancando porta...")
                led.value(1)
                rele.value(1)
                time.sleep(3)
                rele.value(0)
                led.value(0)
                print("[CORE 0] Porta trancada novamente.")
            else:
                print("[CORE 0] ACESSO NEGADO.")
                for _ in range(3):
                    led.value(1)
                    time.sleep_ms(100)
                    led.value(0)
                    time.sleep_ms(100)

        # Core 0 está livre para responder a sensores ou botões físicos
        time.sleep_ms(50)

if __name__ == "__main__":
    main()
