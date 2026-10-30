#!/usr/bin/env python3
"""
Ferramenta Automatizada de Diagnóstico, Upload e Monitoramento do Raspberry Pi Pico
Desenvolvida para o projeto Porta-LAOB.
Usa a biblioteca 'pyserial' nativa do Linux.
"""

import sys
import os
import time
import glob
import serial

class PicoConnection:
    def __init__(self, port=None):
        self.port = port
        self.ser = None

    def find_pico_port(self):
        """Busca portas seriais do Pico (/dev/ttyACM* ou /dev/ttyUSB*)"""
        ports = glob.glob("/dev/ttyACM*") + glob.glob("/dev/ttyUSB*")
        if ports:
            return ports[0]
        return None

    def connect(self, timeout=2):
        if not self.port:
            self.port = self.find_pico_port()
        if not self.port:
            return False

        try:
            self.ser = serial.Serial(self.port, 115200, timeout=timeout)
            return True
        except Exception as e:
            print(f"[ERRO] Falha ao abrir porta {self.port}: {e}")
            return False

    def enter_raw_repl(self):
        """Interrompe execução e entra no modo Raw REPL do MicroPython"""
        if not self.ser: return False

        # Envia Ctrl-C duas vezes para parar qualquer script em execução
        self.ser.write(b"\r\x03\x03")
        time.sleep(0.2)
        self.ser.reset_input_buffer()

        # Envia Ctrl-A para entrar em Raw REPL
        self.ser.write(b"\r\x01")
        time.sleep(0.2)

        resp = self.ser.read_all()
        if b"raw REPL" in resp or b">" in resp:
            return True

        # Tenta mais uma vez
        self.ser.write(b"\r\x01")
        time.sleep(0.2)
        resp = self.ser.read_all()
        return b"raw REPL" in resp or b">" in resp

    def exit_raw_repl(self, reboot=True):
        """Sai do modo Raw REPL e opcionalmente reinicia o Pico (soft reboot)"""
        if not self.ser: return
        if reboot:
            self.ser.write(b"\r\x04") # Ctrl-D (soft reboot)
        else:
            self.ser.write(b"\r\x02") # Ctrl-B (normal REPL)
        time.sleep(0.2)

    def exec_raw(self, code_str):
        """Executa um trecho de código Python diretamente no Pico e retorna a saída"""
        if not self.enter_raw_repl():
            return None, "Falha ao entrar no modo Raw REPL"

        # Envia código terminado com Ctrl-D
        payload = code_str.encode("utf-8") + b"\x04"
        self.ser.write(payload)

        # Resposta no padrão MicroPython: 'OK' + stdout + \x04 + stderr + \x04>
        time.sleep(0.1)
        resp = b""
        start = time.time()
        while time.time() - start < 4:
            if self.ser.in_waiting:
                resp += self.ser.read(self.ser.in_waiting)
                if resp.endswith(b"\x04>"):
                    break
            time.sleep(0.05)

        if resp.startswith(b"OK"):
            parts = resp[2:].split(b"\x04")
            stdout = parts[0].decode("utf-8", errors="replace")
            stderr = parts[1].decode("utf-8", errors="replace") if len(parts) > 1 else ""
            return stdout, stderr
        return None, resp.decode("utf-8", errors="replace")

    def upload_file(self, local_path, remote_name):
        """Grava um arquivo local na memória flash do Pico via Raw REPL"""
        with open(local_path, "rb") as f:
            content = f.read()

        print(f"  -> Enviando '{remote_name}' ({len(content)} bytes)...", end="", flush=True)

        # Divide em chunks para garantir transmissão sem perda
        chunk_size = 256
        init_code = f"__f = open('{remote_name}', 'wb')\n"
        self.exec_raw(init_code)

        for i in range(0, len(content), chunk_size):
            chunk = content[i:i + chunk_size]
            write_code = f"__f.write({repr(chunk)})\n"
            self.exec_raw(write_code)

        self.exec_raw("__f.close()\n")
        print(" [OK]")

    def monitor(self):
        """Lê a saída serial do Pico continuamente"""
        print(f"\n[MONITOR] Conectado a {self.port} (115200 baud). Pressione Ctrl+C para sair.\n")
        print("----------------------------------------------------------------------")
        try:
            while True:
                if self.ser.in_waiting:
                    line = self.ser.read(self.ser.in_waiting).decode("utf-8", errors="replace")
                    print(line, end="", flush=True)
                time.sleep(0.01)
        except KeyboardInterrupt:
            print("\n[MONITOR] Finalizado pelo usuário.")

def cmd_detect():
    conn = PicoConnection()
    port = conn.find_pico_port()
    if port:
        print(f"[SUCESSO] Raspberry Pi Pico detectado na porta: {port}")
        return True
    else:
        print("[AGUARDANDO] Nenhum Raspberry Pi Pico encontrado em /dev/ttyACM* ou /dev/ttyUSB*.")
        return False

def cmd_test():
    conn = PicoConnection()
    if not conn.connect():
        print("[ERRO] Conecte o Raspberry Pi Pico via USB primeiro!")
        return

    print(f"[TESTE] Conectado em {conn.port}. Testando hardware...")
    diag_code = """
import os, sys, machine, gc
print('PLATAFORMA:', sys.platform)
print('VERSAO:', sys.version)
print('CPU_FREQ_MHZ:', machine.freq() // 1000000)
print('FLASH_LIVRE_BYTES:', gc.mem_free())

# Testa se o módulo MFRC522 responde no barramento SPI0
try:
    from machine import Pin, SPI
    spi = SPI(0, baudrate=1000000, sck=Pin(18), mosi=Pin(19), miso=Pin(16))
    cs = Pin(17, Pin.OUT)
    cs.value(0)
    spi.write(bytearray([((0x37 << 1) & 0x7E) | 0x80]))
    ver = spi.read(1)[0]
    cs.value(1)
    print('CHIP_VERSION_REG_0x37: 0x{:02X}'.format(ver))
    if ver in (0x91, 0x92):
        print('MFRC522_STATUS: OK_DETECTADO')
    else:
        print('MFRC522_STATUS: ERRO_VERSAO_INVALIDA')
except Exception as e:
    print('MFRC522_STATUS: FALHA_AO_TESTAR_SPI', e)
"""
    stdout, stderr = conn.exec_raw(diag_code)
    conn.exit_raw_repl(reboot=False)

    if stdout:
        print("\n--- RESULTADO DO DIAGNÓSTICO DO PICO ---")
        print(stdout.strip())
        print("----------------------------------------\n")
    if stderr:
        print("[STDERR]", stderr)

def cmd_upload():
    conn = PicoConnection()
    if not conn.connect():
        print("[ERRO] Conecte o Raspberry Pi Pico via USB primeiro!")
        return

    base_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "micropython"))
    files = ["mfrc522.py", "door_manager.py", "main.py"]

    print(f"\n[UPLOAD] Gravando arquivos no Pico ({conn.port})...")
    conn.enter_raw_repl()

    for fname in files:
        fpath = os.path.join(base_dir, fname)
        if os.path.exists(fpath):
            conn.upload_file(fpath, fname)
        else:
            print(f"  [AVISO] Arquivo {fname} não encontrado em {fpath}!")

    print("[UPLOAD] Concluído com sucesso! Reiniciando o Pico no novo main.py...\n")
    conn.exit_raw_repl(reboot=True)
    conn.monitor()

def main():
    action = sys.argv[1] if len(sys.argv) > 1 else "detect"
    if action == "detect":
        cmd_detect()
    elif action == "test":
        cmd_test()
    elif action == "upload":
        cmd_upload()
    elif action == "monitor":
        conn = PicoConnection()
        if conn.connect():
            conn.monitor()
        else:
            print("[ERRO] Pico não encontrado.")
    else:
        print("Uso: python3 pico_tool.py [detect | test | upload | monitor]")

if __name__ == "__main__":
    main()
