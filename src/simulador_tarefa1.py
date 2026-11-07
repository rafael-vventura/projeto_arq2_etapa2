from pathlib import Path
from ula import ULA

class SimuladorTarefa1:
    def __init__(self):
        self.pc = 0
        self.ir = 0
        # Valores iniciais de teste especificados para a Tarefa 1
        self.reg_a = 0x00000001
        self.reg_b = 0x80000000
        self.ula = ULA()

        # Define caminhos dos arquivos de dados e log
        pasta_raiz = Path(__file__).parent.parent
        self.caminho_entrada = pasta_raiz / 'data' / 'programa_etapa2_tarefa1.txt'
        self.caminho_log = pasta_raiz / 'logs' / 'logFinal_tarefa1.txt'
        self.caminho_log.parent.mkdir(parents=True, exist_ok=True)

    def decodificar_8bits(self):
        # Extrai os 8 bits de controle: SLL8, SRA1, F0, F1, ENA, ENB, INVA, INC
        sll8 = (self.ir >> 7) & 1
        sra1 = (self.ir >> 6) & 1
        f0   = (self.ir >> 5) & 1
        f1   = (self.ir >> 4) & 1
        ena  = (self.ir >> 3) & 1
        enb  = (self.ir >> 2) & 1
        inva = (self.ir >> 1) & 1
        inc  = (self.ir >> 0) & 1
        return sll8, sra1, f0, f1, ena, enb, inva, inc

    def executar(self):
        with open(self.caminho_log, 'w') as log:
            log.write(f"b = {self.reg_b:032b}\n")
            log.write(f"a = {self.reg_a:032b}\n\n")
            log.write("Start of Program\n")

            with open(self.caminho_entrada, 'r') as arq_in:
                for linha in arq_in:
                    linha = linha.strip()
                    if not linha:
                        continue

                    self.ir = int(linha, 2)
                    self.pc += 1

                    sll8, sra1, f0, f1, ena, enb, inva, inc = self.decodificar_8bits()

                    # Bugfix: verifica se ha combinacao proibida de sinais de deslocamento
                    if sll8 == 1 and sra1 == 1:
                        log.write("=" * 60 + "\n")
                        log.write(f"Cycle {self.pc}\n\n")
                        log.write(f"PC = {self.pc}\n")
                        log.write(f"IR = {self.ir:08b}\n")
                        log.write("> Error, invalid control signals.\n")
                        break

                    # Aplica a portaria ENA/ENB nos operandos de entrada
                    a_efetivo = self.reg_a if ena else 0
                    b_efetivo = self.reg_b if enb else 0

                    s, sd, co, n, z = self.ula.operar(
                        f0, f1, inva, inc, a_efetivo, b_efetivo, sll8, sra1
                    )

                    # Registra a saida do ciclo formatada
                    log.write("=" * 60 + "\n")
                    log.write(f"Cycle {self.pc}\n\n")
                    log.write(f"PC = {self.pc}\n")
                    log.write(f"IR = {self.ir:08b}\n")
                    log.write(f"b = {b_efetivo:032b}\n")
                    log.write(f"a = {a_efetivo:032b}\n")
                    log.write(f"s = {s:032b}\n")
                    log.write(f"sd = {sd:032b}\n")
                    log.write(f"n = {n}\n")
                    log.write(f"z = {z}\n")
                    log.write(f"co = {co}\n")

            # Finalizacao padrao do arquivo de log
            log.write("=" * 60 + "\n")
            log.write(f"Cycle {self.pc + 1}\n\n")
            log.write(f"PC = {self.pc + 1}\n")
            log.write("> Line is empty, EOP.\n")

if __name__ == "__main__":
    simulador = SimuladorTarefa1()
    simulador.executar()