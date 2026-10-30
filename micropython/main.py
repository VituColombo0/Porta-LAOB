"""
Porta-LAOB - Sistema Completo de Controle de Acesso para Laboratório
Plataforma: Raspberry Pi Pico (MicroPython)
Arquivo: main.py (executado automaticamente no boot do Pico)

Como usar:
1. Copie todos os arquivos da pasta 'micropython' para a raiz do seu Raspberry Pi Pico.
2. Ao ligar o Pico, o sistema iniciará automaticamente.
3. Aproxime uma tag para liberar a fechadura.
"""

from machine import Pin, SPI
import time
import _thread
from mfrc522 import MFRC522
from door_manager import DoorManager

# Pinagem SPI0 do Raspberry Pi Pico
PIN_SCK    = 18  # Pino 24
PIN_MOSI   = 19  # Pino 25
PIN_MISO   = 16  # Pino 21
PIN_CS     = 17  # Pino 22
PIN_RST    = 22  # Pino 29

# Pinagem dos Periféricos de Acesso
PIN_RELE   = 15  # Pino 20 - Trava solenoide ou relé
PIN_BOTAO  = 13  # Pino 17 - Botoeira de saída interna
PIN_BUZZER = 12  # Pino 16 - Buzzer de feedback (opcional)
PIN_LED    = "LED" # LED onboard do Pico

# Inicializa o gerenciador da porta
door = DoorManager(relay_pin=PIN_RELE, button_pin=PIN_BOTAO,
                   buzzer_pin=PIN_BUZZER, led_pin=PIN_LED)

# Fila/Variável compartilhada entre os núcleos com Lock
thread_lock = _thread.allocate_lock()
tag_buffer = None

def rfid_core1_scanner():
    """
    Núcleo 1 (Core 1): Fica escaneando o leitor RFID em tempo real
    sem travar nem atrasar a CPU do Núcleo 0.
    """
    global tag_buffer
    
    # Inicializa SPI0 no Core 1
    spi = SPI(0, baudrate=1_000_000, polarity=0, phase=0,
              sck=Pin(PIN_SCK), mosi=Pin(PIN_MOSI), miso=Pin(PIN_MISO))
    rdr = MFRC522(spi, PIN_CS, PIN_RST)
    print("[Core 1] Scanner RFID inicializado no Núcleo 1.")

    while True:
        status, _ = rdr.request(rdr.PICC_REQIDL)
        if status == rdr.OK:
            status, uid = rdr.anticoll()
            if status == rdr.OK and len(uid) >= 4:
                uid_str = "{:02X} {:02X} {:02X} {:02X}".format(uid[0], uid[1], uid[2], uid[3])
                
                with thread_lock:
                    tag_buffer = uid_str
                
                rdr.halt()
                # Pequena pausa para evitar múltiplas leituras da mesma aproximação
                time.sleep_ms(800)
                
        time.sleep_ms(25)

def main():
    global tag_buffer
    print("==================================================")
    print("  Porta-LAOB: Iniciando Sistema de Acesso (Pico)  ")
    print("==================================================")

    # Inicia a thread no segundo núcleo (Core 1)
    _thread.start_new_thread(rfid_core1_scanner, ())

    print("[Core 0] Controlador de porta pronto e aguardando eventos.")

    while True:
        # 1. Verifica se houve leitura de cartão pelo Core 1
        tag_lida = None
        with thread_lock:
            if tag_buffer is not None:
                tag_lida = tag_buffer
                tag_buffer = None

        if tag_lida:
            door.process_uid(tag_lida)

        # 2. Verifica se a botoeira física de saída foi pressionada
        door.check_button()

        # O Core 0 pode realizar outras tarefas livremente aqui
        time.sleep_ms(20)

if __name__ == "__main__":
    main()
