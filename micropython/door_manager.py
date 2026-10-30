"""
Porta-LAOB - Gerenciador de Controle de Acesso
Plataforma: Raspberry Pi Pico (MicroPython)

Recursos:
- Persistência de crachás autorizados em JSON na memória flash
- Modo Master: passe o crachá de administrador para cadastrar novos crachás
- Acionamento de relé da trava solenoide/eletroímã
- Suporte a Botoeira de saída (abrir porta por dentro)
- Feedback sonoro com Buzzer (tons de sucesso e erro)
- Registro de logs de acesso em arquivo de texto
"""

from machine import Pin, PWM
import time
import json
import os

class DoorManager:
    def __init__(self, relay_pin=15, button_pin=13, buzzer_pin=12, led_pin="LED",
                 config_file="tags_autorizadas.json", log_file="acessos.log"):
        self.relay = Pin(relay_pin, Pin.OUT)
        self.relay.value(0) # Trava fechada

        self.button = Pin(button_pin, Pin.IN, Pin.PULL_UP) if button_pin is not None else None
        self.led = Pin(led_pin, Pin.OUT)
        self.led.value(0)

        # Configuração do Buzzer (opcional, pode ser None)
        self.buzzer_pin = buzzer_pin
        self.buzzer = None
        if buzzer_pin is not None:
            try:
                self.buzzer = PWM(Pin(buzzer_pin))
                self.buzzer.duty_u16(0)
            except Exception:
                self.buzzer = None

        self.config_file = config_file
        self.log_file = log_file

        # Tag Master padrão para cadastro de novos crachás (pode ser alterada)
        self.master_uid = "MASTER_TAG_LAOB"
        self.admin_mode = False
        self.tags = {}

        self.load_tags()

    def beep(self, freq, duration_ms):
        """Emite um tom sonoro no buzzer"""
        if self.buzzer:
            try:
                self.buzzer.freq(freq)
                self.buzzer.duty_u16(32768) # 50% duty
                time.sleep_ms(duration_ms)
                self.buzzer.duty_u16(0)
            except Exception:
                pass
        else:
            time.sleep_ms(duration_ms)

    def success_feedback(self):
        """Bip agudo e LED verde para acesso liberado"""
        self.led.value(1)
        self.beep(2000, 150)
        self.led.value(0)

    def denied_feedback(self):
        """Três bips graves para acesso negado"""
        for _ in range(3):
            self.led.value(1)
            self.beep(400, 100)
            self.led.value(0)
            time.sleep_ms(80)

    def admin_feedback(self):
        """Tom duplo indicando entrada/saída do modo de cadastro"""
        self.beep(1200, 100)
        time.sleep_ms(50)
        self.beep(1800, 150)

    def load_tags(self):
        """Carrega lista de UIDs autorizados da memória flash"""
        try:
            with open(self.config_file, "r") as f:
                data = json.load(f)
                self.tags = data.get("tags", {})
                self.master_uid = data.get("master_uid", "00 00 00 00")
                print(f"[DoorManager] {len(self.tags)} crachás carregados.")
        except Exception:
            print("[DoorManager] Criando arquivo inicial de tags autorizadas...")
            self.tags = {
                "A1 B2 C3 D4": "Aluno Exemplo 1",
                "43 8A 1F 2C": "Professor LAOB"
            }
            self.save_tags()

    def save_tags(self):
        """Salva a lista de tags no arquivo JSON"""
        try:
            with open(self.config_file, "w") as f:
                json.dump({"master_uid": self.master_uid, "tags": self.tags}, f)
            print("[DoorManager] Tags salvas na flash com sucesso.")
        except Exception as e:
            print(f"[DoorManager] Erro ao salvar tags: {e}")

    def log_access(self, uid, status, user="Desconhecido"):
        """Grava log de evento no arquivo"""
        timestamp = time.time()
        log_line = f"[{timestamp}] UID: {uid} | Status: {status} | Usuario: {user}\n"
        print(f"[LOG] {log_line.strip()}")
        try:
            with open(self.log_file, "a") as f:
                f.write(log_line)
        except Exception:
            pass

    def open_door(self, seconds=3):
        """Destranca a porta pelo tempo especificado"""
        print(f"[PORTA-LAOB] Fechadura acionada por {seconds}s...")
        self.relay.value(1) # Aciona relé
        self.led.value(1)
        time.sleep(seconds)
        self.relay.value(0) # Tranca novamente
        self.led.value(0)
        print("[PORTA-LAOB] Fechadura travada novamente.")

    def process_uid(self, uid):
        """Processa a leitura de uma tag RFID"""
        uid = uid.strip().upper()

        # 1. Verifica se é a Tag Master (Administrador)
        if uid == self.master_uid:
            self.admin_mode = not self.admin_mode
            self.admin_feedback()
            if self.admin_mode:
                print("\n=======================================================")
                print(">>> MODO ADMIN ATIVADO: Aproxime uma tag para cadastrar")
                print("=======================================================\n")
            else:
                print(">>> MODO ADMIN DESATIVADO.")
            return

        # 2. Se estiver em Modo Admin, cadastra a tag que acabou de ser aproximada
        if self.admin_mode:
            if uid in self.tags:
                print(f"[ADMIN] Tag {uid} já estava cadastrada ({self.tags[uid]}).")
            else:
                self.tags[uid] = f"Usuario_Tag_{len(self.tags)+1}"
                self.save_tags()
                print(f"[ADMIN] SUCESSO! Nova tag {uid} cadastrada.")
            self.success_feedback()
            self.admin_mode = False # Sai do modo admin após o cadastro
            return

        # 3. Verificação normal de acesso
        if uid in self.tags:
            user = self.tags[uid]
            print(f"\n[ACESSO PERMITIDO] Bem-vindo(a), {user}! (UID: {uid})")
            self.log_access(uid, "LIBERADO", user)
            self.success_feedback()
            self.open_door()
        else:
            print(f"\n[ACESSO NEGADO] Tag não autorizada: {uid}")
            self.log_access(uid, "NEGADO")
            self.denied_feedback()

    def check_button(self):
        """Verifica se a botoeira física de saída foi pressionada"""
        if self.button and self.button.value() == 0:
            time.sleep_ms(50) # Debounce
            if self.button.value() == 0:
                print("[BOTOEIRA] Botão de saída pressionado internamente!")
                self.log_access("BOTOEIRA_INTERNA", "LIBERADO", "Saida Manual")
                self.success_feedback()
                self.open_door()
