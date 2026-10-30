#ifndef RC522_INTERRUPT_H
#define RC522_INTERRUPT_H

#include <Arduino.h>
#include <SPI.h>
#include <MFRC522.h>

/**
 * @brief Tipo de função de callback disparada quando um cartão é autenticado/lido com sucesso.
 * @param uidStr String contendo o UID em formato Hexadecimal (ex: "A1 B2 C3 D4")
 * @param uidBytes Ponteiro para o array de bytes brutos do UID
 * @param uidSize Quantidade de bytes do UID (geralmente 4 ou 7)
 */
typedef void (*CardDetectedCallback)(const String &uidStr, const byte *uidBytes, byte uidSize);

class RC522_Interrupt : public MFRC522 {
public:
    /**
     * @brief Construtor da classe
     * @param ssPin Pino SPI Slave Select (SDA)
     * @param rstPin Pino Reset (RST)
     * @param irqPin Pino de Interrupção de Hardware conectado ao IRQ do RC522
     */
    RC522_Interrupt(byte ssPin, byte rstPin, byte irqPin);

    /**
     * @brief Inicializa o leitor MFRC522 e configura os registradores de interrupção.
     * @param pushPullMode Se true, configura pino IRQ como Push-Pull (padrão CMOS). Se false, Open-Drain.
     * @return true se a versão do firmware do MFRC522 for válida (ex: 0x91 ou 0x92), false se falhar conexão.
     */
    bool begin(bool pushPullMode = true);

    /**
     * @brief Registra o callback a ser disparado na leitura de uma tag.
     */
    void onCardDetected(CardDetectedCallback callback);

    /**
     * @brief Método principal que deve ser chamado periodicamente no loop() ou em uma task.
     * Executa a verificação da flag de interrupção, lê o cartão, chama o callback e re-arma o receptor.
     * @return true se um cartão foi lido neste ciclo.
     */
    bool update();

    /**
     * @brief Dispara uma nova requisição não-bloqueante (REQA) no transceiver.
     */
    void prepareNextRead();

    /**
     * @brief Limpa as pendências de interrupção nos registradores do chip.
     */
    void clearInterruptFlags();

    /**
     * @brief Obtém a última UID lida em formato String formatada.
     */
    String getLastUidString() const;

    /**
     * @brief Obtém o pino IRQ configurado.
     */
    byte getIrqPin() const { return _irqPin; }

    /**
     * @brief Rotina interna chamada pela ISR externa
     */
    void handleISR();

private:
    byte _irqPin;
    volatile bool _interruptTriggered;
    CardDetectedCallback _callback;
    String _lastUid;
    unsigned long _lastReadTime;

    void setupInterruptRegisters(bool pushPullMode);
    static void defaultISR();
    static RC522_Interrupt* _instance;
};

#endif // RC522_INTERRUPT_H
