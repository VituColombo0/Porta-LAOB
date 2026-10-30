#include "RC522_Interrupt.h"

RC522_Interrupt* RC522_Interrupt::_instance = nullptr;

RC522_Interrupt::RC522_Interrupt(byte ssPin, byte rstPin, byte irqPin)
    : MFRC522(ssPin, rstPin),
      _irqPin(irqPin),
      _interruptTriggered(false),
      _callback(nullptr),
      _lastUid(""),
      _lastReadTime(0) {
    _instance = this;
}

void RC522_Interrupt::defaultISR() {
    if (_instance != nullptr) {
        _instance->handleISR();
    }
}

void RC522_Interrupt::handleISR() {
    _interruptTriggered = true;
}

bool RC522_Interrupt::begin(bool pushPullMode) {
    // Inicializa a interface SPI e o chip MFRC522
    PCD_Init();

    // Valida versão do hardware (0x91 ou 0x92 são versões oficiais da NXP)
    byte version = PCD_ReadRegister(VersionReg);
    if (version == 0x00 || version == 0xFF) {
        // Falha de comunicação SPI ou módulo não conectado
        return false;
    }

    // Configura o pino de hardware no MCU
    pinMode(_irqPin, INPUT_PULLUP);

    // Configura registradores internos de interrupção do MFRC522
    setupInterruptRegisters(pushPullMode);

    // Conecta a ISR externa no MCU (gatilho de borda de descida - FALLING)
    attachInterrupt(digitalPinToInterrupt(_irqPin), defaultISR, FALLING);

    // Limpa transientes iniciais sem travamentos (elimina o bug do while(!bNewInt))
    clearInterruptFlags();
    _interruptTriggered = false;

    // Dispara a primeira escuta assíncrona
    prepareNextRead();

    return true;
}

void RC522_Interrupt::setupInterruptRegisters(bool pushPullMode) {
    // 1. Limpa todas as pendências de interrupções anteriores
    clearInterruptFlags();

    // 2. Configura DivIEnReg (0x03)
    // Bit 7 (IRQPushPull): 1 = Push-Pull (3-state CMOS), 0 = Open-Drain
    byte divVal = pushPullMode ? 0x80 : 0x00;
    PCD_WriteRegister(DivIEnReg, divVal);

    // 3. Configura ComIEnReg (0x02)
    // 0xA0: Bit 7 (IRqInv) e Bit 5 (TxIEn) / Bit 4 (RxIEn).
    // Habilita a propagação das interrupções de recepção para o pino físico IRQ
    PCD_WriteRegister(ComIEnReg, 0xA0);
}

void RC522_Interrupt::clearInterruptFlags() {
    // Escrever 0x7F no ComIrqReg limpa todos os bits de interrupção ativos
    PCD_WriteRegister(ComIrqReg, 0x7F);
    PCD_WriteRegister(DivIrqReg, 0x7F);
}

void RC522_Interrupt::prepareNextRead() {
    // Envia o comando REQA assincronamente pelo transmissor de RF
    PCD_WriteRegister(FIFODataReg, PICC_CMD_REQA);
    PCD_WriteRegister(CommandReg, PCD_Transceive);
    PCD_WriteRegister(BitFramingReg, 0x87); // StartSend = 1, 7 bits
}

void RC522_Interrupt::onCardDetected(CardDetectedCallback callback) {
    _callback = callback;
}

bool RC522_Interrupt::update() {
    unsigned long now = millis();

    // Se houve trigger de interrupção por hardware
    if (_interruptTriggered) {
        _interruptTriggered = false;

        // Tenta ler o número de série (UID) do cartão que respondeu
        if (PICC_ReadCardSerial()) {
            // Monta string formatada em hexadecimal
            String uidStr = "";
            for (byte i = 0; i < uid.size; i++) {
                if (uid.uidByte[i] < 0x10) uidStr += "0";
                uidStr += String(uid.uidByte[i], HEX);
                if (i < uid.size - 1) uidStr += " ";
            }
            uidStr.toUpperCase();
            _lastUid = uidStr;
            _lastReadTime = now;

            // Dispara o callback se configurado
            if (_callback != nullptr) {
                _callback(uidStr, uid.uidByte, uid.size);
            }

            // Encerra a comunicação com a tag e limpa estados criptográficos
            PICC_HaltA();
            PCD_StopCrypto1();

            // Limpa as flags e arma novamente para o próximo cartão
            clearInterruptFlags();
            prepareNextRead();
            return true;
        } else {
            // Interrupção espúria ou erro de colisão na leitura
            clearInterruptFlags();
            prepareNextRead();
        }
    }

    // Watchdog de segurança: se passar mais de 1000ms sem eventos,
    // re-arretira e re-dispara o transceiver para evitar desarmamento por ruído.
    if (now - _lastReadTime > 1000) {
        clearInterruptFlags();
        prepareNextRead();
        _lastReadTime = now;
    }

    return false;
}

String RC522_Interrupt::getLastUidString() const {
    return _lastUid;
}
