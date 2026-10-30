"""
MicroPython MFRC522 RFID Reader Driver para Raspberry Pi Pico
Adaptado e otimizado para o projeto Porta-LAOB.
"""

from machine import Pin, SPI
import time

class MFRC522:
    # Registradores do MFRC522
    CommandReg     = 0x01
    ComIEnReg      = 0x02
    DivIEnReg      = 0x03
    ComIrqReg      = 0x04
    DivIrqReg      = 0x05
    ErrorReg       = 0x06
    Status1Reg     = 0x07
    Status2Reg     = 0x08
    FIFODataReg    = 0x09
    FIFOLevelReg   = 0x0A
    WaterLevelReg  = 0x0B
    ControlReg     = 0x0C
    BitFramingReg  = 0x0D
    CollReg        = 0x0E
    ModeReg        = 0x11
    TxModeReg      = 0x12
    RxModeReg      = 0x13
    TxControlReg   = 0x14
    TxASKReg       = 0x15
    TxSelReg       = 0x16
    RxSelReg       = 0x17
    RxThresholdReg = 0x18
    DemodReg       = 0x19
    MfTxReg        = 0x1C
    MfRxReg        = 0x1D
    SerialSpeedReg = 0x1F
    CRCResultRegH  = 0x21
    CRCResultRegL  = 0x22
    ModWidthReg    = 0x24
    RFCfgReg       = 0x26
    GsNReg         = 0x27
    CWGsPReg       = 0x28
    ModGsPReg      = 0x29
    TModeReg       = 0x2A
    TPrescalerReg  = 0x2B
    TReloadRegH    = 0x2C
    TReloadRegL    = 0x2D
    TCounterValRegH= 0x2E
    TCounterValRegL= 0x2F
    TestSel1Reg    = 0x31
    TestSel2Reg    = 0x32
    TestPinEnReg   = 0x33
    TestPinValueReg= 0x34
    TestBusReg     = 0x35
    AutoTestReg    = 0x36
    VersionReg     = 0x37
    AnalogTestReg  = 0x38

    # Comandos do chip PCD
    PCD_IDLE       = 0x00
    PCD_AUTHENT    = 0x0E
    PCD_RECEIVE    = 0x08
    PCD_TRANSMIT   = 0x04
    PCD_TRANSCEIVE = 0x0C
    PCD_RESETPHASE = 0x0F
    PCD_CALCCRC    = 0x03

    # Comandos PICC (Cartão)
    PICC_REQIDL    = 0x26
    PICC_REQALL    = 0x52
    PICC_ANTICOLL  = 0x93
    PICC_ANTICOLL2 = 0x95 # Cascade level 2 (para tags de 7 bytes)
    PICC_SETECTTAG = 0x93
    PICC_AUTHENT1A = 0x60
    PICC_AUTHENT1B = 0x61
    PICC_READ      = 0x30
    PICC_WRITE     = 0xA0
    PICC_DECREMENT = 0xC0
    PICC_INCREMENT = 0xC1
    PICC_RESTORE   = 0xC2
    PICC_TRANSFER  = 0xB0
    PICC_HALT      = 0x50

    # Status de Retorno
    OK             = 0
    NOTAGERR       = 1
    ERR            = 2

    def __init__(self, spi, cs_pin, rst_pin):
        self.spi = spi
        self.cs = Pin(cs_pin, Pin.OUT)
        self.rst = Pin(rst_pin, Pin.OUT)
        self.cs.value(1)
        self.rst.value(1)
        self.init()

    def _write_reg(self, reg, val):
        self.cs.value(0)
        self.spi.write(bytearray([(reg << 1) & 0x7E, val]))
        self.cs.value(1)

    def _read_reg(self, reg):
        self.cs.value(0)
        self.spi.write(bytearray([((reg << 1) & 0x7E) | 0x80]))
        val = self.spi.read(1)
        self.cs.value(1)
        return val[0]

    def _set_bit_mask(self, reg, mask):
        current = self._read_reg(reg)
        self._write_reg(reg, current | mask)

    def _clear_bit_mask(self, reg, mask):
        current = self._read_reg(reg)
        self._write_reg(reg, current & (~mask))

    def reset(self):
        self._write_reg(self.CommandReg, self.PCD_RESETPHASE)

    def init(self):
        self.rst.value(0)
        time.sleep_ms(10)
        self.rst.value(1)
        time.sleep_ms(10)

        self.reset()
        self._write_reg(self.TModeReg, 0x8D)
        self._write_reg(self.TPrescalerReg, 0x3E)
        self._write_reg(self.TReloadRegL, 30)
        self._write_reg(self.TReloadRegH, 0)
        self._write_reg(self.TxASKReg, 0x40)
        self._write_reg(self.ModeReg, 0x3D)
        self.antenna_on()

    def get_version(self):
        """Retorna a versão do chip. Valores esperados: 0x91 (v1.0) ou 0x92 (v2.0)"""
        return self._read_reg(self.VersionReg)

    def antenna_on(self):
        val = self._read_reg(self.TxControlReg)
        if (val & 0x03) != 0x03:
            self._set_bit_mask(self.TxControlReg, 0x03)

    def antenna_off(self):
        self._clear_bit_mask(self.TxControlReg, 0x03)

    def _to_card(self, command, send_data):
        back_data = []
        back_len = 0
        status = self.ERR
        irq_en = 0x00
        wait_irq = 0x00

        if command == self.PCD_AUTHENT:
            irq_en = 0x12
            wait_irq = 0x10
        elif command == self.PCD_TRANSCEIVE:
            irq_en = 0x77
            wait_irq = 0x30

        self._write_reg(self.ComIEnReg, irq_en | 0x80)
        self._clear_bit_mask(self.ComIrqReg, 0x80)
        self._set_bit_mask(self.FIFOLevelReg, 0x80)
        self._write_reg(self.CommandReg, self.PCD_IDLE)

        for byte in send_data:
            self._write_reg(self.FIFODataReg, byte)

        self._write_reg(self.CommandReg, command)
        if command == self.PCD_TRANSCEIVE:
            self._set_bit_mask(self.BitFramingReg, 0x80)

        i = 2000
        n = 0
        while True:
            n = self._read_reg(self.ComIrqReg)
            i -= 1
            # Correção crítica do bug lógico de '~' em Python:
            # Sai do laço se: estourou o timeout (i == 0) OU ocorreu erro (bit 0) OU recebeu interrupção esperada
            if (i == 0) or (n & 0x01) or (n & wait_irq):
                break

        self._clear_bit_mask(self.BitFramingReg, 0x80)

        if i != 0:
            if (self._read_reg(self.ErrorReg) & 0x1B) == 0x00:
                status = self.OK
                if n & irq_en & 0x01:
                    status = self.NOTAGERR
                if command == self.PCD_TRANSCEIVE:
                    fifo_len = self._read_reg(self.FIFOLevelReg)
                    last_bits = self._read_reg(self.ControlReg) & 0x07
                    if last_bits != 0:
                        back_len = (fifo_len - 1) * 8 + last_bits
                    else:
                        back_len = fifo_len * 8
                    if fifo_len == 0:
                        fifo_len = 1
                    for _ in range(fifo_len):
                        back_data.append(self._read_reg(self.FIFODataReg))
            else:
                status = self.ERR

        return status, back_data, back_len

    def request(self, req_mode=0x26):
        self._write_reg(self.BitFramingReg, 0x07)
        status, back_data, back_bits = self._to_card(self.PCD_TRANSCEIVE, [req_mode])
        if status != self.OK or back_bits != 0x10:
            status = self.ERR
        return status, back_bits

    def anticoll(self, level=1):
        """
        Executa a sequência de anticollisão.
        level=1: padrão para 4 bytes (Cascade Level 1).
        level=2: para tags de 7 bytes (Cascade Level 2).
        """
        cmd = self.PICC_ANTICOLL if level == 1 else self.PICC_ANTICOLL2
        self._write_reg(self.BitFramingReg, 0x00)
        status, back_data, _ = self._to_card(self.PCD_TRANSCEIVE, [cmd, 0x20])
        if status == self.OK:
            if len(back_data) == 5:
                # Verificação de checksum BCC
                checksum = back_data[0] ^ back_data[1] ^ back_data[2] ^ back_data[3]
                if checksum != back_data[4]:
                    status = self.ERR
            else:
                status = self.ERR
        return status, back_data

    def read_uid(self):
        """
        Helper de alto nível para ler o UID completo de uma tag.
        Suporta tanto tags clássicas de 4 bytes (Mifare 1K) quanto de 7 bytes (NTAG / Ultralight).
        Retorna (status, uid_list)
        """
        status, _ = self.request(self.PICC_REQIDL)
        if status != self.OK:
            return self.ERR, []

        status, uid1 = self.anticoll(level=1)
        if status != self.OK:
            return self.ERR, []

        # Se o primeiro byte for 0x88 (CT - Cascade Tag), significa que a tag tem 7 bytes
        if uid1[0] == 0x88:
            status, uid2 = self.anticoll(level=2)
            if status == self.OK:
                # Monta os 7 bytes: 3 bytes do nível 1 + 4 bytes do nível 2
                full_uid = [uid1[1], uid1[2], uid1[3], uid2[0], uid2[1], uid2[2], uid2[3]]
                return self.OK, full_uid
            return self.OK, uid1[:4]

        return self.OK, uid1[:4]

    def halt(self):
        self._write_reg(self.BitFramingReg, 0x00)
        self._to_card(self.PCD_TRANSCEIVE, [self.PICC_HALT, 0])
        self._clear_bit_mask(self.Status2Reg, 0x08)
