"""
Porta-LAOB - Gerenciador Completo de Controle de Acesso
Plataforma: Raspberry Pi Pico / Pico W (MicroPython)

Recursos Integrados:
- Persistência de crachás autorizados em JSON na memória flash
- Modo Master: crachá administrador para cadastrar/excluir tags no local
- Acionamento de relé configurável (Normalmente Aberto ou Normalmente Fechado)
- Suporte a Botoeira de saída interna
- Sensor Magnético de Porta (aviso sonoro de porta esquecida aberta)
- Feedback sonoro com Buzzer PWM (tons distintos)
- Display OLED I2C opcional (detecção automática plug-and-play)
- Registro de auditoria com rotação de log
- Compatibilidade universal com Pico e Pico W (LED onboard automático)
"""

from machine import Pin, PWM
import time
import json
import os

class DoorManager:
    def __init__(self,
                 relay_pin=15,
                 button_pin=13,
                 buzzer_pin=12,
                 sensor_pin=11,
                 led_pin=None,
                 relay_active_high=True,
                 config_file="tags_autorizadas.json",
                 log_file="acessos.log",
                 i2c_bus=None):

        self.relay_active_high = relay_active_high
        self.relay = Pin(relay_pin, Pin.OUT)
        self._set_relay(False) # Garante porta travada no boot

        # Botoeira de saída interna (ativa em nível baixo com pull-up)
        self.button = Pin(button_pin, Pin.IN, Pin.PULL_UP) if button_pin is not None else None

        # Sensor magnético de abertura de porta (Reed Switch: 0 = fechada, 1 = aberta)
        self.sensor = Pin(sensor_pin, Pin.IN, Pin.PULL_UP) if sensor_pin is not None else None
        self.door_opened_time = None
        self.door_alarm_active = False

        # LED Onboard com detecção automática entre Pico (GP25) e Pico W ("LED")
        self.led = self._setup_led(led_pin)

        # Buzzer PWM (opcional)
        self.buzzer = None
        if buzzer_pin is not None:
            try:
                self.buzzer = PWM(Pin(buzzer_pin))
                self.buzzer.duty_u16(0)
            except Exception:
                self.buzzer = None

        # Display OLED I2C (opcional)
        self.oled = None
        if i2c_bus is not None:
            self._setup_oled(i2c_bus)

        self.config_file = config_file
        self.log_file = log_file

        self.master_uid = "MASTER_TAG_LAOB"
        self.admin_mode = False
        self.tags = {}

        self.load_tags()
        self.display_message("Porta LAOB", "Aproxime cracha")

    def _setup_led(self, led_pin):
        if led_pin is not None:
            try:
                p = Pin(led_pin, Pin.OUT)
                p.value(0)
                return p
            except Exception:
                pass
        try:
            p = Pin("LED", Pin.OUT)
            p.value(0)
            return p
        except Exception:
            try:
                p = Pin(25, Pin.OUT)
                p.value(0)
                return p
            except Exception:
                return None

    def _setup_oled(self, i2c):
        try:
            import ssd1306
            self.oled = ssd1306.SSD1306_I2C(128, 64, i2c)
            self.oled.fill(0)
            self.oled.text("Porta-LAOB", 20, 20)
            self.oled.show()
        except Exception:
            self.oled = None

    def display_message(self, line1="", line2="", line3=""):
        if self.oled:
            try:
                self.oled.fill(0)
                if line1: self.oled.text(line1, 0, 10)
                if line2: self.oled.text(line2, 0, 28)
                if line3: self.oled.text(line3, 0, 46)
                self.oled.show()
            except Exception:
                pass

    def _set_relay(self, unlock):
        """Liga ou desliga a trava eletrônica respeitando o tipo de relé"""
        if self.relay_active_high:
            self.relay.value(1 if unlock else 0)
        else:
            self.relay.value(0 if unlock else 1)

    def _set_led(self, state):
        if self.led:
            self.led.value(1 if state else 0)

    def beep(self, freq, duration_ms):
        """Gera tom no buzzer se disponível"""
        if self.buzzer:
            try:
                self.buzzer.freq(freq)
                self.buzzer.duty_u16(32768) # 50% duty
                time.sleep_ms(duration_ms)
                self.buzzer.duty_u16(0)
            except Exception:
                time.sleep_ms(duration_ms)
        else:
            time.sleep_ms(duration_ms)

    def success_feedback(self):
        """1 bip agudo e LED aceso"""
        self._set_led(True)
        self.beep(2200, 150)
        self._set_led(False)

    def denied_feedback(self):
        """3 bips graves de alerta"""
        for _ in range(3):
            self._set_led(True)
            self.beep(450, 100)
            self._set_led(False)
            time.sleep_ms(80)

    def admin_feedback(self):
        """Tom melódico para modo de configuração"""
        self.beep(1200, 100)
        time.sleep_ms(40)
        self.beep(1800, 150)

    def load_tags(self):
        """Carrega banco de tags autorizadas do arquivo JSON na flash"""
        try:
            with open(self.config_file, "r") as f:
                data = json.load(f)
                self.tags = data.get("tags", {})
                self.master_uid = data.get("master_uid", "MASTER_TAG_LAOB")
                print(f"[DoorManager] {len(self.tags)} cracha(s) carregado(s).")
        except Exception:
            print("[DoorManager] Criando arquivo padrao tags_autorizadas.json...")
            self.tags = {
                "A1 B2 C3 D4": "Aluno Exemplo 1",
                "43 8A 1F 2C": "Professor LAOB"
            }
            self.master_uid = "00 00 00 00"
            self.save_tags()

    def save_tags(self):
        try:
            with open(self.config_file, "w") as f:
                json.dump({"master_uid": self.master_uid, "tags": self.tags}, f)
            print("[DoorManager] Banco de tags salvo na flash com sucesso.")
        except Exception as e:
            print(f"[DoorManager] Erro ao salvar tags: {e}")

    def log_access(self, uid, status, user="Desconhecido"):
        """Grava auditoria no log com protecao contra estouro de flash"""
        timestamp = time.time()
        log_line = f"[{timestamp}] UID: {uid} | Status: {status} | User: {user}\n"
        print(f"[LOG] {log_line.strip()}")

        try:
            # Rotacao de log se passar de 30KB
            try:
                st = os.stat(self.log_file)
                if st[6] > 30000:
                    os.rename(self.log_file, self.log_file + ".old")
            except OSError:
                pass

            with open(self.log_file, "a") as f:
                f.write(log_line)
        except Exception:
            pass

    def open_door(self, seconds=3):
        """Destranca a fechadura pelo tempo configurado"""
        print(f"[PORTA-LAOB] Fechadura destrancada por {seconds}s...")
        self._set_relay(True)
        self._set_led(True)

        # Espera o tempo ou trava antecipadamente se a porta foi aberta e fechada
        start_ms = time.ticks_ms()
        door_was_opened = False

        while time.ticks_diff(time.ticks_ms(), start_ms) < (seconds * 1000):
            if self.sensor:
                if self.sensor.value() == 1:
                    door_was_opened = True
                elif door_was_opened and self.sensor.value() == 0:
                    # Porta abriu e fechou antes do tempo: tranca imediatamente por seguranca!
                    time.sleep_ms(300)
                    break
            time.sleep_ms(50)

        self._set_relay(False)
        self._set_led(False)
        print("[PORTA-LAOB] Fechadura travada novamente.")
        self.display_message("Porta LAOB", "Aproxime cracha")

    def process_uid(self, uid):
        """Processa a leitura de uma tag RFID"""
        uid = uid.strip().upper()

        # 1. Modo Administrador (Master Tag)
        if uid == self.master_uid or self.master_uid == "00 00 00 00":
            if self.master_uid == "00 00 00 00":
                # Primeiro crachá passado vira o Master definitivo!
                self.master_uid = uid
                self.save_tags()
                print(f"[ADMIN] Tag {uid} registrada como MASTER!")
                self.admin_feedback()
                self.display_message("MASTER DEFINIDO", uid)
                time.sleep(2)
                self.display_message("Porta LAOB", "Aproxime cracha")
                return

            self.admin_mode = not self.admin_mode
            self.admin_feedback()
            if self.admin_mode:
                print("\n>>> MODO ADMIN ATIVADO: Aproxime a tag para cadastrar/remover")
                self.display_message("MODO CADASTRO", "Aproxime tag")
            else:
                print(">>> MODO ADMIN DESATIVADO.")
                self.display_message("Porta LAOB", "Aproxime cracha")
            return

        # 2. Cadastro / Remoção em Modo Admin
        if self.admin_mode:
            if uid in self.tags:
                nome_removido = self.tags.pop(uid)
                self.save_tags()
                print(f"[ADMIN] Tag {uid} ({nome_removido}) REMOVIDA!")
                self.display_message("TAG REMOVIDA", nome_removido)
            else:
                novo_nome = f"Usuario_{len(self.tags)+1}"
                self.tags[uid] = novo_nome
                self.save_tags()
                print(f"[ADMIN] SUCESSO! Tag {uid} cadastrada como '{novo_nome}'.")
                self.display_message("TAG CADASTRADA", novo_nome, uid)

            self.success_feedback()
            time.sleep(2)
            self.admin_mode = False
            self.display_message("Porta LAOB", "Aproxime cracha")
            return

        # 3. Verificação de Acesso Normal
        if uid in self.tags:
            user = self.tags[uid]
            print(f"\n[ACESSO PERMITIDO] Bem-vindo(a), {user}! (UID: {uid})")
            self.display_message("ACESSO LIBERADO", user)
            self.log_access(uid, "LIBERADO", user)
            self.success_feedback()
            self.open_door()
        else:
            print(f"\n[ACESSO NEGADO] Tag nao autorizada: {uid}")
            self.display_message("ACESSO NEGADO", "Tag invalida")
            self.log_access(uid, "NEGADO")
            self.denied_feedback()
            time.sleep(1)
            self.display_message("Porta LAOB", "Aproxime cracha")

    def check_inputs(self):
        """Verifica a botoeira de saída e o sensor de porta aberta"""
        # Botoeira física de saída
        if self.button and self.button.value() == 0:
            time.sleep_ms(40) # Debounce
            if self.button.value() == 0:
                print("[BOTOEIRA] Abertura manual solicitada!")
                self.display_message("SAIDA MANUAL", "Porta Aberta")
                self.log_access("BOTOEIRA", "LIBERADO", "Saida Manual")
                self.success_feedback()
                self.open_door()

        # Sensor de porta esquecida aberta (aviso de 20 segundos)
        if self.sensor:
            if self.sensor.value() == 1: # Porta aberta
                if self.door_opened_time is None:
                    self.door_opened_time = time.ticks_ms()
                elif time.ticks_diff(time.ticks_ms(), self.door_opened_time) > 20000:
                    # Mais de 20 segundos aberta: alerta sonoro
                    self.beep(800, 80)
                    self._set_led(True)
                    time.sleep_ms(80)
                    self._set_led(False)
            else:
                self.door_opened_time = None
