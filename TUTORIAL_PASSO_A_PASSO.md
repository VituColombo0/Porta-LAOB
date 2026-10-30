# 📖 Guia Passo a Passo: Sistema de Acesso Porta-LAOB no Raspberry Pi Pico

Este guia foi elaborado para que qualquer pessoa consiga montar, gravar e colocar em funcionamento o controle de acesso por RFID no **Raspberry Pi Pico** (ou Pico W) sem dores de cabeça.

---

## 🛠️ 1. Materiais Necessários

1. **Placa Microcontroladora:** Raspberry Pi Pico ou Pico W
2. **Leitor RFID:** MFRC522 (13.56 MHz) com tags/cartões Mifare
3. **Módulo Relé (1 ou 2 canais):** Para acionar a fechadura elétrica (solenoide ou eletroímã)
4. **Fechadura Elétrica:** 12V (solenoide) ou eletroímã com fonte externa de 12V
5. **Botão de Saída (Botoeira tipo Push Button):** Para liberar a porta por dentro
6. **Buzzer Passivo ou Ativo (Opcional):** Para feedback sonoro (bips de acesso permitido/negado)
7. **Jumpers (Fios Fêmea-Macho e Fêmea-Fêmea)**

---

## 🔌 2. Esquema de Ligação Elétrica (Pinagem)

> ⚠️ **REGRA DE OURO:** O leitor MFRC522 **só suporta 3.3V**. O Raspberry Pi Pico opera em 3.3V nativo. **NUNCA** ligue o VCC do leitor nos 5V (VBUS).

### Diagrama de Pinagem no Raspberry Pi Pico (Pinos Físicos)

```text
                           RASPBERRY PI PICO
                             +-----------+
              (SPI0 RX) GP0 -| 1      40 |- VBUS (5V da USB)
                        GP1 -| 2      39 |- VSYS
                        GND -| 3      38 |- GND <------------------ GND do MFRC522 / Relé
                        GP2 -| 4      37 |- 3V3_EN
                        GP3 -| 5      36 |- 3V3(OUT) <------------- 3.3V do MFRC522 (VCC)
                        GP4 -| 6      35 |- ADC_VREF
                        GP5 -| 7      34 |- GP28
                        GND -| 8      33 |- GND
                        GP6 -| 9      32 |- GP27
                        GP7 -| 10     31 |- GP26
                        GP8 -| 11     30 |- RUN
                        GP9 -| 12     29 |- GP22 <----------------- RST do MFRC522
                        GND -| 13     28 |- GND
                       GP10 -| 14     27 |- GP21
(Sensor de Porta)      GP11 -| 15     26 |- GP20
(Buzzer PWM)           GP12 -| 16     25 |- GP19 <----------------- MOSI do MFRC522
(Botoeira de Saída)    GP13 -| 17     24 |- GP18 <----------------- SCK do MFRC522
(IRQ do MFRC522)       GP14 -| 18     23 |- GND
(Relé da Trava)        GP15 -| 19     22 |- GP17 <----------------- SDA (CS) do MFRC522
(SPI0 MISO)            GP16 -| 20     21 |- GP16 <----------------- MISO do MFRC522
                             +-----------+
```

### Tabela Resumida de Conexões

| Dispositivo | Pino no Módulo | Pino no Raspberry Pi Pico | Observações |
| :--- | :--- | :--- | :--- |
| **MFRC522** | **3.3V (VCC)** | **Pino 36 (3V3_OUT)** | Alimentação 3.3V regulada |
| **MFRC522** | **GND** | **Pino 38 (GND)** | Terra comum |
| **MFRC522** | **RST** | **Pino 29 (GP22)** | Reset do leitor |
| **MFRC522** | **SDA (SS/CS)** | **Pino 22 (GP17)** | Chip Select (SPI0 CSn) |
| **MFRC522** | **SCK** | **Pino 24 (GP18)** | Clock SPI (SPI0 SCK) |
| **MFRC522** | **MOSI** | **Pino 25 (GP19)** | Transmissão de dados (SPI0 TX) |
| **MFRC522** | **MISO** | **Pino 20 ou 21 (GP16)** | Recepção de dados (SPI0 RX) |
| **MFRC522** | **IRQ** | **Pino 18 (GP14)** | Para interrupção por hardware |
| **Módulo Relé** | **IN / Sinal** | **Pino 19 (GP15)** | Aciona a trava da porta |
| **Módulo Relé** | **VCC** | **Pino 36 (3.3V)** ou **Pino 40 (5V)** | Depende do modelo do relé |
| **Módulo Relé** | **GND** | **Pino 38 (GND)** | Terra comum |
| **Botoeira** | **Terminal 1** | **Pino 17 (GP13)** | Botão para abrir por dentro |
| **Botoeira** | **Terminal 2** | **GND** | Puxa o pino para terra ao apertar |
| **Buzzer** | **Positivo (+)** | **Pino 16 (GP12)** | Som de sucesso/erro |
| **Buzzer** | **Negativo (-)** | **GND** | Terra |

---

## 💻 3. Como Instalar o MicroPython no Pico (em 2 minutos)

Se o seu Raspberry Pi Pico já roda MicroPython, pule para o **Passo 4**.

1. Segure o botão branco **BOOTSEL** no Raspberry Pi Pico e conecte o cabo USB no computador.
2. O computador reconhecerá uma unidade de disco chamada **`RPI-RP2`**.
3. Baixe o firmware oficial `.uf2`:
   * [MicroPython para Raspberry Pi Pico](https://micropython.org/download/rp2-pico/)
   * [MicroPython para Raspberry Pi Pico W](https://micropython.org/download/rp2-pico-w/)
4. Arraste o arquivo `.uf2` para dentro da unidade `RPI-RP2`. O Pico reiniciará automaticamente pronto com MicroPython!

---

## 🚀 4. Como Carregar os Arquivos no Pico (Usando o Thonny)

1. Baixe e instale o [Thonny IDE](https://thonny.org/).
2. Conecte o Pico ao USB e abra o Thonny.
3. No canto inferior direito do Thonny, clique e selecione:
   **`MicroPython (Raspberry Pi Pico)`**.
4. No painel de arquivos à esquerda (Arquivos do computador), navegue até a pasta:
   `/home/lirool/.gemini/antigravity-ide/scratch/Porta-LAOB/micropython/`
5. Selecione os 3 arquivos essenciais:
   * **`mfrc522.py`**
   * **`door_manager.py`**
   * **`main.py`**
6. Clique com o botão direito sobre eles e escolha **"Fazer upload para /"** (Upload to /).
7. Pronto! Os arquivos agora estão na raiz da memória flash do Raspberry Pi Pico.

---

## 🎯 5. Como o Sistema Funciona no Dia a Dia

### A. Primeiro Boot e Cadastro do Crachá Mestre (Admin)
1. Ao ligar a placa, o leitor inicializa.
2. O **primeiro crachá que você aproximar** será automaticamente gravado como o **CRACHÁ MASTER (ADMINISTRADOR)**!
3. O buzzer dará um bipe duplo confirmando.

### B. Como Cadastrar Novos Alunos / Usuários
1. Aproxime o **Crachá Master**:
   * O sistema entrará em **MODO CADASTRO** (aviso no terminal ou tela).
2. Aproxime o crachá do aluno/pesquisador que deseja autorizar:
   * O sistema salvará o UID no arquivo `tags_autorizadas.json` na memória flash.
   * O buzzer tocará o bipe agudo de sucesso.
   * A porta volta automaticamente ao modo normal.

### C. Como Remover uma Tag Cadastrada
1. Aproxime o **Crachá Master** (entra em modo cadastro).
2. Aproxime a tag que deseja remover:
   * O sistema detecta que ela já existia e a exclui do banco.

### D. Acesso Liberado
1. Quando uma pessoa cadastrada aproxima o crachá:
   * O relé é acionado (destranca a porta por 3 segundos).
   * O LED onboard acende.
   * O buzzer toca 1 bipe agudo.
   * O evento é registrado no arquivo `acessos.log`.

### E. Acesso Negado
1. Se uma tag desconhecida for aproximada:
   * A trava permanece trancada.
   * O buzzer toca 3 bips curtos de erro.
   * O evento é gravado no log como tentativa negada.

### F. Abertura por Dentro (Botoeira)
1. Pressionar a botoeira no pino GP13 destranca a fechadura por 3 segundos para saída de quem está dentro da sala.

---

## 🛡️ 6. Solução de Problemas Comuns (Troubleshooting)

* **O terminal mostra `[Core 1 - AVISO] Chip respondeu versao 0x00 ou 0xFF`:**
  * Significa que o Raspberry Pi Pico não está conseguindo falar com o RC522.
  * Verifique se o fio **3.3V** está firme no Pino 36 (3V3_OUT).
  * Verifique se os fios **SCK (GP18)**, **MOSI (GP19)** e **MISO (GP16)** não estão trocados.
  * Verifique se o GND está compartilhado.

* **O relé fica sempre aberto e desliga ao ler o cartão:**
  * Alguns módulos de relé funcionam com lógica invertida (Ativo em Nível Baixo / Active Low).
  * Para corrigir, no arquivo `main.py`, mude:
    `relay_active_high=False`

* **As tags cadastradas somem quando desligo o Pico?**
  * Não! As tags ficam permanentemente gravadas no arquivo `tags_autorizadas.json` na memória flash do próprio Pico.
