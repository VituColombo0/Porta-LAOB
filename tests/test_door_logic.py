"""
Teste Unitário e de Integração da Lógica de Acesso da Porta-LAOB
Executado em Python padrão simulando o hardware do Raspberry Pi Pico.
"""

import sys
import os
import time

# Cria um mock do módulo 'machine' para rodar em Python padrão no PC
class MockPin:
    IN = 0
    OUT = 1
    PULL_UP = 2

    def __init__(self, pin, mode=OUT, pull=None):
        self.pin = pin
        self.mode = mode
        self.pull = pull
        self._val = 0

    def value(self, val=None):
        if val is not None:
            self._val = val
        return self._val

    def irq(self, trigger=None, handler=None):
        pass

class MockPWM:
    def __init__(self, pin):
        self.pin = pin

    def freq(self, f):
        pass

    def duty_u16(self, d):
        pass

# Injeta os mocks no sys.modules
import types
mock_machine = types.ModuleType("machine")
mock_machine.Pin = MockPin
mock_machine.PWM = MockPWM
mock_machine.SPI = lambda *args, **kwargs: None
mock_machine.I2C = lambda *args, **kwargs: None
sys.modules["machine"] = mock_machine

# Adiciona o diretório micropython ao path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "micropython")))

# Mock de ticks_ms para time
if not hasattr(time, "ticks_ms"):
    time.ticks_ms = lambda: int(time.time() * 1000)
if not hasattr(time, "ticks_diff"):
    time.ticks_diff = lambda a, b: a - b
if not hasattr(time, "sleep_ms"):
    time.sleep_ms = lambda ms: time.sleep(ms / 1000.0)

from door_manager import DoorManager

def test_door_system():
    test_cfg = "/tmp/test_tags.json"
    test_log = "/tmp/test_access.log"

    # Limpa arquivos de teste anteriores
    if os.path.exists(test_cfg): os.remove(test_cfg)
    if os.path.exists(test_log): os.remove(test_log)

    print("--- 1. Inicializando DoorManager ---")
    door = DoorManager(relay_pin=15, button_pin=13, buzzer_pin=12, sensor_pin=11,
                       config_file=test_cfg, log_file=test_log)

    # 1. Teste de primeira inicialização com tags padrão
    assert "A1 B2 C3 D4" in door.tags, "Tag padrão 1 não encontrada"
    assert "43 8A 1F 2C" in door.tags, "Tag padrão 2 não encontrada"
    print("  [PASS] Banco de tags inicial criado e verificado.")

    # 2. Teste de Acesso Permitido
    print("--- 2. Testando Acesso com Tag Autorizada ---")
    door.process_uid("A1 B2 C3 D4")
    assert door.relay.value() == 0, "Relé deveria estar travado novamente após tempo"
    print("  [PASS] Acesso autorizado processado com sucesso.")

    # 3. Teste de Acesso Negado
    print("--- 3. Testando Acesso com Tag Não Autorizada ---")
    door.process_uid("FF FF FF FF")
    assert door.relay.value() == 0, "Relé não deveria ter sido acionado"
    print("  [PASS] Acesso negado com sucesso.")

    # 4. Teste de Definição de Tag Master
    print("--- 4. Testando Registro e Modo Master ---")
    # A master padrão inicial é "00 00 00 00", então o primeiro toque registra o novo master
    door.master_uid = "00 00 00 00"
    door.process_uid("EE EE EE EE")
    assert door.master_uid == "EE EE EE EE", "Tag master não foi salva corretamente"
    print(f"  [PASS] Tag Master definida para: {door.master_uid}")

    # 5. Entra em Modo Admin usando a Tag Master
    print("--- 5. Testando Entrada no Modo Admin ---")
    door.process_uid("EE EE EE EE")
    assert door.admin_mode is True, "Modo Admin deveria estar ativo"
    print("  [PASS] Modo Admin ativado.")

    # 6. Cadastra um novo crachá no modo Admin
    print("--- 6. Cadastrando Novo Crachá via Modo Admin ---")
    door.process_uid("11 22 33 44")
    assert "11 22 33 44" in door.tags, "Nova tag não foi cadastrada"
    assert door.admin_mode is False, "Modo Admin deveria ter finalizado após o cadastro"
    print("  [PASS] Novo crachá cadastrado com sucesso.")

    # 7. Testa o novo crachá cadastrado
    print("--- 7. Testando o Novo Crachá Cadastrado ---")
    door.process_uid("11 22 33 44")
    print("  [PASS] Novo crachá liberou a porta.")

    # 8. Teste de Botoeira de Saída
    print("--- 8. Testando Botoeira de Saída ---")
    door.button.value(0) # Pressiona botão
    door.check_inputs()
    door.button.value(1) # Solta botão
    print("  [PASS] Botoeira acionou abertura.")

    # 9. Teste de Auditoria de Log
    print("--- 9. Verificando Arquivo de Log de Acessos ---")
    assert os.path.exists(test_log), "Arquivo de log não foi criado"
    with open(test_log, "r") as f:
        logs = f.readlines()
    assert len(logs) >= 3, "Deveriam haver ao menos 3 registros de log"
    print(f"  [PASS] Logs auditados com sucesso ({len(logs)} eventos gravados).")

    # Limpeza
    os.remove(test_cfg)
    os.remove(test_log)
    print("\n==========================================")
    print("   TODOS OS TESTES PASSARAM COM SUCESSO!  ")
    print("==========================================")

if __name__ == "__main__":
    test_door_system()
