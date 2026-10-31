#!/usr/bin/env python3
"""
Monitor Contínuo do Leitor RFID no Raspberry Pi Pico
Executa no Pico e escuta em tempo real a detecção do chip e de tags/crachás.
"""

import sys
import time
import serial

SERIAL_PORT = "/dev/ttyACM0"
BAUD_RATE = 115200

def main():
    try:
        ser = serial.Serial(SERIAL_PORT, BAUD_RATE, timeout=1)
    except Exception as e:
        print(f"Erro ao abrir serial {SERIAL_PORT}: {e}")
        sys.exit(1)

    print("=" * 65)
    print(" 📡 INICIANDO MONITOR CONTÍNUO DO LEITOR RFID-RC522 NO PICO")
    print("=" * 65)
    print("Aguardando comunicação do chip MFRC522 (Pressione Ctrl+C para sair)...")

    # Código MicroPython a ser executado no Pico
    mpy_code = """
import time
from machine import Pin, SPI
from mfrc522 import MFRC522

spi = SPI(0, baudrate=1000000, polarity=0, phase=0,
          sck=Pin(18), mosi=Pin(19), miso=Pin(16))

reader = MFRC522(spi, cs_pin=17, rst_pin=22)

# LED on-board para sinalizar
try:
    led = Pin('LED', Pin.OUT)
except:
    led = Pin(25, Pin.OUT)

chip_detected = False
last_msg = 0

while True:
    v = reader.get_version()
    
    if v in (0x88, 0x91, 0x92):
        if not chip_detected:
            chip_detected = True
            print(f'>>> CHIP_DETECTADO: MFRC522 Firmware 0x{v:02X} OK! <<<')
            led.value(1)
        
        # Tenta ler tag
        status, tag_type = reader.request(reader.PICC_REQIDL)
        if status == reader.OK:
            status, uid = reader.anticoll()
            if status == reader.OK:
                uid_str = ' '.join([f'{b:02X}' for b in uid])
                print(f'>>> TAG_DETECTADA! UID: {uid_str} <<<')
                # Pisca LED de confirmacao
                for _ in range(2):
                    led.value(0)
                    time.sleep_ms(80)
                    led.value(1)
                    time.sleep_ms(80)
                time.sleep_ms(400)
    else:
        if chip_detected:
            chip_detected = False
            led.value(0)
            print('>>> ALERTA: Conexao com o chip perdida! <<<')
        
        if time.time() - last_msg >= 3:
            print(f'[Aguardando sinal] Resposta atual do barramento: 0x{v:02X} (Esperado: 0x91 ou 0x92)')
            last_msg = time.time()
            
    time.sleep_ms(150)
"""
    # Envia para o MicroPython via Raw REPL
    ser.write(b'\x03\x03\x01')
    time.sleep(0.15)
    ser.read_all()
    
    ser.write(mpy_code.encode('utf-8') + b'\x04')
    
    try:
        while True:
            line = ser.readline()
            if line:
                decoded = line.decode('utf-8', errors='replace').strip()
                if decoded:
                    print(decoded)
    except KeyboardInterrupt:
        print("\nMonitor interrompido pelo usuário.")
    finally:
        ser.write(b'\x03\x02') # Ctrl+C e Ctrl+B
        ser.close()

if __name__ == '__main__':
    main()
