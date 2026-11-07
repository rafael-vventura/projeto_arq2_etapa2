from pathlib import Path
from ula import ULA

class SimuladorTarefa2:
    def __init__(self):
        self.ciclo = 1
        self.circuito_ula = ULA()

        # Banco de 10 registradores da microarquitetura Mic-1
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
        # Le os valores iniciais dos registradores no arquivo de configuracao
        with open(self.caminho_regs, 'r') as arq:
            for linha in arq:
                if "=" in linha:
                    nome, valor = linha.strip().split("=")
                    self.banco_regs[nome.strip().lower()] = int(valor.strip(), 2)

    def decodificar_microinstrucao(self, palavra):
        # Fatia a palavra de 21 bits em ULA (8 bits), Barramento C (9 bits) e Barramento B (4 bits)
        ctrl_ula = int(palavra[0:8], 2)
        ctrl_bus_c = int(palavra[8:17], 2)
        ctrl_bus_b = int(palavra[17:21], 2)
        return ctrl_ula, ctrl_bus_c, ctrl_bus_b

    def obter_barramento_b(self, codigo_b):
        # Mapeamento do decodificador de 4 bits para o barramento B
        mapa_fontes = {
            0: "mdr", 1: "pc", 2: "mbr", 3: "mbru",
            4: "sp", 5: "lv", 6: "cpp", 7: "opc", 8: "tos"
        }
        nome_reg = mapa_fontes.get(codigo_b, "none")
        if nome_reg == "none":
            return 0, nome_reg

        # Leitura generica do registrador (tratamento de sinal sera refinado)
        if nome_reg in ["mbr", "mbru"]:
            dado_b = self.banco_regs["mbr"] & 0xFF
        else:
            dado_b = self.banco_regs[nome_reg]

        return dado_b, nome_reg

    def aplicar_barramento_c(self, ctrl_bus_c, valor_sd):
        # Mapeamento dos 9 registradores de destino no Barramento C
        lista_c = ["mar", "mdr", "pc", "sp", "lv", "cpp", "tos", "opc", "h"]
        for indice, reg in enumerate(lista_c):
            if (ctrl_bus_c >> indice) & 1:
                self.banco_regs[reg] = valor_sd & 0xFFFFFFFF

    def formatar_registradores(self):
        # Formata o estado binario (8 bits para MBR e 32 bits para os demais)
        linhas = []
        for r in self.ordem_exibicao:
            v = self.banco_regs[r]
            linhas.append(f"{r} = {v:08b}" if r == "mbr" else f"{r} = {v:032b}")
        return "\n".join(linhas)

if __name__ == "__main__":
    simulador = SimuladorTarefa2()
    simulador.carregar_estado_inicial()
    print("Estado inicial dos registradores:")
    print(simulador.formatar_registradores())