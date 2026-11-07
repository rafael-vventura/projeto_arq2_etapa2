class ULA:
    def __init__(self, largura_bits=32):
        self.largura_bits = largura_bits
        # Mascara de 32 bits (0xFFFFFFFF) para simular o limite fisico dos registradores
        self.mascara_32bits = (1 << largura_bits) - 1

    def operar(self, f0, f1, inva, inc, entrada_a, entrada_b, sll8=0, sra1=0):
        # Inversao bit a bit condicional da entrada A
        if inva == 1:
            entrada_a = (~entrada_a) & self.mascara_32bits

        # Mapeamento das 4 operacoes internas via seletor F0 e F1
        codigo_op = (f0 << 1) | f1
        vai_um = 0

        if codigo_op == 0:
            resultado_s = entrada_a & entrada_b
        elif codigo_op == 1:
            resultado_s = entrada_a | entrada_b
        elif codigo_op == 2:
            resultado_s = entrada_b
        else:
            soma = entrada_a + entrada_b + inc
            resultado_s = soma & self.mascara_32bits
            if soma > self.mascara_32bits:
                vai_um = 1

        # Estagio do Deslocador (Shifter)
        resultado_sd = resultado_s
        if sll8 == 1:
            resultado_sd = (resultado_s << 8) & self.mascara_32bits
        elif sra1 == 1:
            bit_sinal = (resultado_s >> (self.largura_bits - 1)) & 1
            if bit_sinal == 1:
                resultado_sd = (resultado_s >> 1) | (1 << (self.largura_bits - 1))
            else:
                resultado_sd = resultado_s >> 1

        # Calculo das flags de condicao a partir da saida Sd
        flag_z = 1 if resultado_sd == 0 else 0
        flag_n = (resultado_sd >> (self.largura_bits - 1)) & 1

        return resultado_s, resultado_sd, vai_um, flag_n, flag_z