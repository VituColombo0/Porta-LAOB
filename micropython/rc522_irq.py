"""
Driver de Interrupção por Hardware (IRQ) para RFID-RC522 no Raspberry Pi Pico
Desenvolvido especificamente para o projeto Porta-LAOB.
"""

from machine import Pin, SPI
import time
from mfrc522 import MFRC522

class RC522_Pico_IRQ:
    def __init__(self, spi, cs_pin=17, rst_pin=22, irq_pin=14, push_pull=True):
        self.rdr = MFRC522(spi, cs_pin, rst_pin)
        self.irq_pin_num = irq_pin
        self.push_pull = push_pull
        self.irq_pin = Pin(irq_pin, Pin.IN, Pin.PULL_UP)
        self._card_flag = False
        self._callback = None
        self._last_uid = ""
        self._last_read_ms = 0
        self._setup_registers()

    def _isr_handler(self, pin):
        # A ISR precisa ser ultra rápida e JAMAIS executar SPI ou alocações
        self._card_flag = True

    def _setup_registers(self):
        # 1. Limpa interrupções pendentes
        self.clear_irq_flags()

        # 2. Configura modo elétrico do pino IRQ:
        # Bit 7 = 1 (Push-Pull CMOS padrão) ou 0 (Open-Drain com pull-up)
        div_val = 0x80 if self.push_pull else 0x00
        self.rdr._write_reg(self.rdr.DivIEnReg, div_val)

        # 3. Habilita a propagação das interrupções de Rx/Idle para o pino físico
        # 0xA0 = Bit 7 (IRqInv) | Bit 5 (TxIEn) / Bit 4 (RxIEn)
        self.rdr._write_reg(self.rdr.ComIEnReg, 0xA0)

        # 4. Conecta a interrupção de hardware do GPIO no Pico (borda de descida)
        self.irq_pin.irq(trigger=Pin.IRQ_FALLING, handler=self._isr_handler)

        # 5. Prepara primeira escuta
        self.prepare_next_read()

    def clear_irq_flags(self):
        self.rdr._write_reg(self.rdr.ComIrqReg, 0x7F)
        self.rdr._write_reg(self.rdr.DivIrqReg, 0x7F)

    def prepare_next_read(self):
        # Envia comando de interrogação REQA de forma assíncrona
        self.rdr._write_reg(self.rdr.FIFODataReg, self.rdr.PICC_REQIDL)
        self.rdr._write_reg(self.rdr.CommandReg, self.rdr.PCD_TRANSCEIVE)
        self.rdr._write_reg(self.rdr.BitFramingReg, 0x87)

    def on_card(self, callback_func):
        """Registra função de callback que recebe (uid_str, uid_bytes)"""
        self._callback = callback_func

    def update(self):
        """
        Método não-bloqueante a ser chamado no loop principal.
        Retorna True se um cartão foi detectado e processado.
        """
        now = time.ticks_ms()

        if self._card_flag:
            self._card_flag = False

            # Desativa temporariamente a ISR durante a leitura SPI para evitar reentrância
            self.irq_pin.irq(handler=None)

            # Executa leitura robusta de UID (suporta 4 e 7 bytes)
            status, uid = self.rdr.read_uid()
            if status == self.rdr.OK and len(uid) >= 4:
                uid_str = " ".join("{:02X}".format(b) for b in uid)
                self._last_uid = uid_str
                self._last_read_ms = now

                # Dispara o callback cadastrado
                if self._callback:
                    self._callback(uid_str, uid)

                # Desliga a comunicação com a tag lida
                self.rdr.halt()

            # Limpa flags de interrupção e reativa a ISR
            self.clear_irq_flags()
            self.prepare_next_read()
            self.irq_pin.irq(trigger=Pin.IRQ_FALLING, handler=self._isr_handler)
            return True

        # Watchdog preventivo: re-arma o transceiver a cada 1000ms se estiver ocioso
        if time.ticks_diff(now, self._last_read_ms) > 1000:
            self.clear_irq_flags()
            self.prepare_next_read()
            self._last_read_ms = now

        return False
