"""
Porta-LAOB - Sistema Completo de Controle de Acesso
Plataforma: Raspberry Pi Pico / Pico W (MicroPython)
Arquivo: main.py (executado automaticamente no boot)

Pinagem Padronizada no Pico:
  MFRC522      Raspberry Pi Pico (RP2040)
  -----------------------------------------
  3.3V (VCC)-> Pino 36 (3V3 OUT)
  GND       -> Pino 38 (GND)
  RST       -> Pino 29 (GP22)
  IRQ       -> Pino 19 (GP14) [Para modo IRQ]
  MISO (RX) -> Pino 21 (GP16 - SPI0 RX)
  MOSI (TX) -> Pino 25 (GP19 - SPI0 TX)
  SCK       -> Pino 24 (GP18 - SPI0 SCK)
  SDA (CS)  -> Pino 22 (GP17 - SPI0 CSn)
  -----------------------------------------
  RELÉ      -> Pino 20 (GP15) - Trava da Porta
  BOTOEIRA  -> Pino 17 (GP13) - Botão de Saída Interna
  BUZZER    -> Pino 16 (GP12) - Feedback Sonoro PWM
  SENSOR    -> Pino 15 (GP11) - Sensor de Porta Fechada (Opcional)
"""

from machine import Pin, SPI, I2C
import time
import _thread
from mfrc522 import MFRC522
from door_manager import DoorManager

# Definições de Pinos
PIN_SCK     = 18
PIN_MOSI    = 19
PIN_MISO    = 16
PIN_CS      = 17
PIN_RST     = 22
PIN_RELE    = 15
PIN_BOTAO   = 13
PIN_BUZZER  = 12
PIN_SENSOR  = 11

# Tenta inicializar I2C para Display OLED opcional no GP8/GP9 (I2C0)
i2c_bus = None
try:
    i2c_bus = I2C(0, sda=Pin(8), scl=Pin(9), freq=400000)
    devices = i2c_bus.scan()
    if 0x3C not in devices and 0x3D not in devices:
        i2c_bus = None
except Exception:
    i2c_bus = None

# Inicializa o Gerenciador da Porta
door = DoorManager(relay_pin=PIN_RELE,
                   button_pin=PIN_BOTAO,
                   buzzer_pin=PIN_BUZZER,
                   sensor_pin=PIN_SENSOR,
                   relay_active_high=True,
                   i2c_bus=i2c_bus)

# Lock de sincronização entre os núcleos
thread_lock = _thread.allocate_lock()
tag_buffer = None

def rfid_core1_scanner():
    """
    Núcleo 1 (Core 1): Roda a leitura em paralelo no segundo processador.
    Totalmente isolado do Core 0, sem travar nem atrasar a fechadura.
    """
    global tag_buffer

    # Inicializa SPI0 no Core 1
    spi = SPI(0, baudrate=1_000_000, polarity=0, phase=0,
              sck=Pin(PIN_SCK), mosi=Pin(PIN_MOSI), miso=Pin(PIN_MISO))

    rdr = None
    while rdr is None:
        try:
            rdr = MFRC522(spi, PIN_CS, PIN_RST)
            version = rdr.get_version()
            if version in (0x91, 0x92):
                print(f"[Core 1] MFRC522 detectado com sucesso! Firmware: 0x{version:02X}")
            else:
                print(f"[Core 1 - AVISO] Chip respondeu versao 0x{version:02X}. Verifique fios SPI/3.3V!")
        except Exception as e:
            print(f"[Core 1] Tentando reconectar leitor: {e}")
            time.sleep_ms(1500)

    print("[Core 1] Scanner RFID ativo e pronto para leituras.")

    while True:
        try:
            status, uid = rdr.read_uid()
            if status == rdr.OK and len(uid) >= 4:
                uid_str = " ".join("{:02X}".format(b) for b in uid)

                with thread_lock:
                    tag_buffer = uid_str

                rdr.halt()
                # Pausa para evitar múltiplas leituras em um único encosto
                time.sleep_ms(800)

        except Exception as ex:
            # Protege a thread para nunca morrer mesmo com ruídos elétricos
            pass

        time.sleep_ms(25)

def main():
    global tag_buffer
    print("==================================================")
    print("       Porta-LAOB - Controle de Acesso (RP2040)   ")
    print("==================================================")
    print("Iniciando arquitetura Dual-Core (Núcleo 0 + Núcleo 1)...")

    # Dispara a varredura do leitor no segundo núcleo (Core 1)
    _thread.start_new_thread(rfid_core1_scanner, ())

    print("[Core 0] Controlador de porta pronto. Aguardando aproximacao de cracha...")

    while True:
        # 1. Verifica se houve leitura capturada pelo Core 1
        tag_lida = None
        with thread_lock:
            if tag_buffer is not None:
                tag_lida = tag_buffer
                tag_buffer = None

        if tag_lida:
            door.process_uid(tag_lida)

        # 2. Verifica botoeira física de saída e sensor de porta aberta
        door.check_inputs()

        time.sleep_ms(20)

if __name__ == "__main__":
    main()
