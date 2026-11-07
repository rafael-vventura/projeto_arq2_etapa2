from pathlib import Path
from ula import ULA

class SimuladorTarefa2:
    def __init__(self):
        self.ciclo = 1
        self.circuito_ula = ULA()

        # Banco dos 10 registadores da arquitetura Mic-1
        self.banco_regs = {
            "mar": 0, "mdr": 0, "pc": 0, "mbr": 0,
            "sp": 0, "lv": 0, "cpp": 0, "tos": 0,
            "opc": 0, "h": 0
        }
        self.ordem_exibicao = ["mar", "mdr", "pc", "mbr", "sp", "lv", "cpp", "tos", "opc", "h"]

        pasta_raiz = Path(__file__).parent.parent
        self.caminho_regs = pasta_raiz / 'data' / 'registradores_etapa2_tarefa2.txt'
        self.caminho_prog = pasta_raiz / 'data' / 'programa_etapa2_tarefa2.txt'
        self.caminho_log = pasta_raiz / 'logs' / 'logFinal_tarefa2.txt'
        self.caminho_log.parent.mkdir(parents=True, exist_ok=True)

    def carregar_estado_inicial(self):
        # Carrega o ficheiro de configuracao inicial dos registadores
        with open(self.caminho_regs, 'r') as arq:
            for linha in arq:
                if "=" in linha:
                    nome, valor = linha.strip().split("=")
                    self.banco_regs[nome.strip().lower()] = int(valor.strip(), 2)

    def decodificar_microinstrucao(self, palavra):
        # Fatia a microinstrucao de 21 bits nos 3 campos de controlo
        ctrl_ula = int(palavra[0:8], 2)
        ctrl_bus_c = int(palavra[8:17], 2)
        ctrl_bus_b = int(palavra[17:21], 2)
        return ctrl_ula, ctrl_bus_c, ctrl_bus_b

    def obter_barramento_b(self, codigo_b):
        # Decodificador de 4 bits para selecao do registador fonte no Barramento B
        mapa_fontes = {
            0: "mdr", 1: "pc", 2: "mbr", 3: "mbru",
            4: "sp", 5: "lv", 6: "cpp", 7: "opc", 8: "tos"
        }
        nome_reg = mapa_fontes.get(codigo_b, "none")
        if nome_reg == "none":
            return 0, nome_reg

        # Bugfix: extensao de sinal preservando complemento para dois em mbr e zeros em mbru
        if nome_reg == "mbru":
            return self.banco_regs["mbr"] & 0x000000FF, nome_reg
        elif nome_reg == "mbr":
            val = self.banco_regs["mbr"]
            if (val & 0b10000000) != 0:
                return val | 0xFFFFFF00, nome_reg
            return val & 0x000000FF, nome_reg
        else:
            return self.banco_regs[nome_reg], nome_reg

    def obter_nomes_barramento_c(self, ctrl_bus_c):
        # Mapeamento estrito dos bits 8 a 0 para os registadores do Barramento C
        lista_c = ["mar", "mdr", "pc", "sp", "lv", "cpp", "tos", "opc", "h"]
        destinos = []
        for i in reversed(range(9)):
            if (ctrl_bus_c >> i) & 1:
                destinos.append(lista_c[i])
        return destinos

    def aplicar_barramento_c(self, ctrl_bus_c, valor_sd):
        # Bugfix: gravacao paralela nos registadores ativados no Barramento C
        lista_c = ["mar", "mdr", "pc", "sp", "lv", "cpp", "tos", "opc", "h"]
        for indice, reg in enumerate(lista_c):
            if (ctrl_bus_c >> indice) & 1:
                self.banco_regs[reg] = valor_sd & 0xFFFFFFFF

    def formatar_registradores(self):
        # Formata o estado dos 10 registadores (mbr em 8 bits e restantes em 32 bits)
        linhas = []
        for r in self.ordem_exibicao:
            v = self.banco_regs[r]
            linhas.append(f"{r} = {v:08b}" if r == "mbr" else f"{r} = {v:032b}")
        return "\n".join(linhas)

    def executar(self):
        instrucoes = []
        with open(self.caminho_prog, 'r') as arq_in:
            for linha in arq_in:
                linha = linha.strip()
                if linha:
                    instrucoes.append(linha)

        with open(self.caminho_log, 'w') as log:
            # Cabecalho do log com todas as instrucoes do programa
            log.write("\n".join(instrucoes) + "\n")
            log.write("\n" + "=" * 53 + "\n")

            # Exibicao do estado inicial carregado
            self.carregar_estado_inicial()
            log.write("> Initial register states\n")
            log.write(self.formatar_registradores() + "\n")

            log.write("\n" + "=" * 53 + "\n")
            log.write("Start of program\n")
            log.write("=" * 53 + "\n")

            # Processamento ciclo a ciclo
            for inst in instrucoes:
                ctrl_ula, ctrl_bus_c, ctrl_bus_b = self.decodificar_microinstrucao(inst)

                log.write(f"Cycle {self.ciclo}\n")
                log.write(f"ir = {inst[0:8]} {inst[8:17]} {inst[17:21]}\n\n")

                valor_b, nome_b = self.obter_barramento_b(ctrl_bus_b)
                nomes_c = self.obter_nomes_barramento_c(ctrl_bus_c)
                str_c = ", ".join(nomes_c) if nomes_c else "none"

                log.write(f"b_bus = {nome_b}\n")
                log.write(f"c_bus = {str_c}\n\n")

                log.write("> Registers before instruction\n")
                log.write(self.formatar_registradores() + "\n\n")

                # Decomposicao dos 8 bits de controlo da ULA
                sll8 = (ctrl_ula >> 7) & 1
                sra1 = (ctrl_ula >> 6) & 1
                f0   = (ctrl_ula >> 5) & 1
                f1   = (ctrl_ula >> 4) & 1
                ena  = (ctrl_ula >> 3) & 1
                enb  = (ctrl_ula >> 2) & 1
                inva = (ctrl_ula >> 1) & 1
                inc  = (ctrl_ula >> 0) & 1

                # Entrada A fixada permanentemente em H
                dado_a = self.banco_regs["h"] if ena else 0
                dado_b = valor_b if enb else 0

                s, sd, co, n, z = self.circuito_ula.operar(
                    f0, f1, inva, inc, dado_a, dado_b, sll8, sra1
                )

                self.aplicar_barramento_c(ctrl_bus_c, sd)

                log.write("> Registers after instruction\n")
                log.write(self.formatar_registradores() + "\n")
                log.write("=" * 53 + "\n")

                self.ciclo += 1

            # Finalizacao padrao com o numero do ultimo ciclo valido executado
            log.write(f"Cycle {self.ciclo - 1}\n")
            log.write("No more lines, EOP.\n")

if __name__ == "__main__":
    simulador = SimuladorTarefa2()
    simulador.executar()