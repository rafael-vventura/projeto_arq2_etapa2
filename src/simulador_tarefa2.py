from pathlib import Path
from ula import ULA

class SimuladorTarefa2:
    def __init__(self):
        self.ciclo = 1
        self.circuito_ula = ULA()

        # Banco dos 10 registadores da Mic-1
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
        # Carrega os valores iniciais dos registadores a partir do ficheiro
        with open(self.caminho_regs, 'r') as arq:
            for linha in arq:
                if "=" in linha:
                    nome, valor = linha.strip().split("=")
                    self.banco_regs[nome.strip().lower()] = int(valor.strip(), 2)

    def decodificar_microinstrucao(self, palavra):
        # Separa a microinstrucao de 21 bits em controlo da ULA, Barramento C e Barramento B
        ctrl_ula = int(palavra[0:8], 2)
        ctrl_bus_c = int(palavra[8:17], 2)
        ctrl_bus_b = int(palavra[17:21], 2)
        return ctrl_ula, ctrl_bus_c, ctrl_bus_b

    def obter_barramento_b(self, codigo_b):
        # Mapeamento dos 4 bits de selecao da fonte para o Barramento B
        mapa_fontes = {
            0: "mdr", 1: "pc", 2: "mbr", 3: "mbru",
            4: "sp", 5: "lv", 6: "cpp", 7: "opc", 8: "tos"
        }
        nome_reg = mapa_fontes.get(codigo_b, "none")
        if nome_reg == "none":
            return 0, nome_reg

        # Leitura inicial simples (o refinamento de extensao de sinal fica para o commit 6)
        if nome_reg in ["mbr", "mbru"]:
            dado_b = self.banco_regs["mbr"] & 0xFF
        else:
            dado_b = self.banco_regs[nome_reg]

        return dado_b, nome_reg

    def obter_nomes_barramento_c(self, ctrl_bus_c):
        # Mapeamento dos nomes dos registadores com escrita ativada no Barramento C
        lista_c = ["mar", "mdr", "pc", "sp", "lv", "cpp", "tos", "opc", "h"]
        destinos = []
        for i in reversed(range(9)):
            if (ctrl_bus_c >> i) & 1:
                destinos.append(lista_c[i])
        return destinos

    def aplicar_barramento_c(self, ctrl_bus_c, valor_sd):
        # Atualiza os registadores habilitados pelo Barramento C com o resultado deslocado
        lista_c = ["mar", "mdr", "pc", "sp", "lv", "cpp", "tos", "opc", "h"]
        for indice, reg in enumerate(lista_c):
            if (ctrl_bus_c >> indice) & 1:
                self.banco_regs[reg] = valor_sd & 0xFFFFFFFF

    def formatar_registradores(self):
        # Gera o bloco em texto com os 10 registadores formatados em binario
        linhas = []
        for r in self.ordem_exibicao:
            v = self.banco_regs[r]
            linhas.append(f"{r} = {v:08b}" if r == "mbr" else f"{r} = {v:032b}")
        return "\n".join(linhas)

    def executar(self):
        # Le todas as instrucoes do programa
        instrucoes = []
        with open(self.caminho_prog, 'r') as arq_in:
            for linha in arq_in:
                linha = linha.strip()
                if linha:
                    instrucoes.append(linha)

        with open(self.caminho_log, 'w') as log:
            # 1. Cabecalho inicial: lista das instrucoes a executar
            log.write("\n".join(instrucoes) + "\n")
            log.write("\n" + "=" * 53 + "\n")

            # 2. Estado inicial dos registadores
            self.carregar_estado_inicial()
            log.write("> Initial register states\n")
            log.write(self.formatar_registradores() + "\n")

            log.write("\n" + "=" * 53 + "\n")
            log.write("Start of program\n")
            log.write("=" * 53 + "\n")

            # 3. Execucao ciclo a ciclo
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

                # Decomposicao dos sinais de controlo da ULA
                sll8 = (ctrl_ula >> 7) & 1
                sra1 = (ctrl_ula >> 6) & 1
                f0   = (ctrl_ula >> 5) & 1
                f1   = (ctrl_ula >> 4) & 1
                ena  = (ctrl_ula >> 3) & 1
                enb  = (ctrl_ula >> 2) & 1
                inva = (ctrl_ula >> 1) & 1
                inc  = (ctrl_ula >> 0) & 1

                # Entrada A e soldada permanentemente no registador H
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

            # 4. Encerramento com o ciclo final
            log.write(f"Cycle {self.ciclo - 1}\n")
            log.write("No more lines, EOP.\n")

if __name__ == "__main__":
    simulador = SimuladorTarefa2()
    simulador.executar()