import sys
import numpy as np

'''
jeito burro
def get_pressure_fuzzy(volume, temperature):
    if volume == "pequeno" and temperature == "baixa":
        pressao = "baixa"
    elif volume == "pequeno" and temperature == "média":
        pressao = "baixa"
    elif volume == "pequeno" and temperature == "alta":
        pressao = "média"
    elif volume == "médio" and temperature == "baixa":
        pressao = "baixa"
    elif volume == "médio" and temperature == "média":
        pressao = "média"
    elif volume == "médio" and temperature == "alta":
        pressao = "alta"
    elif volume == "grande" and temperature == "baixa":
        pressao = "média"
    elif volume == "grande" and temperature == "média":
        pressao = "alta"
    elif volume == "grande" and temperature == "alta":
        pressao = "alta"
    return pressao
'''

def triangular(x, a, b, c):
    """
    Função para calcular a função triangular.
    :param a: limite inferior
    :param b: limite superior
    :param c: valor a ser avaliado
    :return: valor da função triangular
    """
    if a <= x <= b:
        return (x - a) / (b - a)
    elif b <= x <= c:
        return (c - x) / (c - b)
    return 0

def descendent_trapezoid(x, a, b, c):
    """
    Função para calcular a função trapezoidal.
    :param a: limite superior
    :param b: ponto em que a função começa a decrescer
    :param c: limite inferior
    :return: valor da função trapezoidal
    """
    if a <= x <= b:
        return 1
    elif b <= x <= c:
        return (c - x) / (c - b)
    return 0
    
def ascendent_trapezoid(x, a, b, c):
    """
    Função para calcular a função trapezoidal.
    :param a: limite inferior
    :param b: ponto em que a função termina de crescer
    :param c: limite superior
    :return: valor da função trapezoidal
    """
    if a <= x <= b:
        return (x - a) / (b - a)
    elif b <= x <= c:
        return 1

    if a <= x <= b:
        return (x - a) / (b - a)
    elif b <= x <= c:
        return (c - x) / (c - b)
    return 0

class Variavel:
    """
    Classe para representar o volume da caldeira.
    :param input: valor de entrada
    :param min_value: valor mínimo
    :param max_value: valor máximo
    :param conjunto_termos: conjunto de termos, deve-se colocar em ordem proporcional à intensidade da variável
    :param universo_discurso: universo de discurso
    :param fracao: fração do universo de discurso, para separar os 
    valores que representam o limite do que é pequeno, médio e grande
    """
    def __init__(self, min_value, max_value, conjunto_termos):
        self.input = input
        self.min_value = min_value
        self.max_value = max_value
        self.conjunto_termos = conjunto_termos
        self.pontos_discretizacao = np.linspace(min_value, max_value, 500)
        self.fracao = max_value / (2*len(self.conjunto_termos) - 1)


    def _verificar_se_pertence_universo_discurso(self, input):
        """
        Função para verificar se o valor de entrada pertence ao universo de discurso.
        :return: True se pertence, False caso contrário
        """
        return self.min_value <= input <= self.max_value
    

    def fuzzificar_variavel(self, input):
        if not self._verificar_se_pertence_universo_discurso(input):
            raise ValueError(f"Valor de entrada {input} não pertence ao universo de discurso.")
        """
        Função para fuzzificar a variável.
        :return: dicionário com os valores de pertinência
        """
        return {self.conjunto_termos[0]: descendent_trapezoid(input, self.fracao*1, self.fracao*2, self.fracao*3),
                self.conjunto_termos[1]: triangular(input, self.fracao*2, self.fracao*3, self.fracao*4),
                self.conjunto_termos[2]: ascendent_trapezoid(input, self.fracao*3, self.fracao*4, self.fracao*5)}
        # por isso, é necessário por em ordem os conjuntos de termos, para que a função funcione corretamente
    

class VariavelTemperatura(Variavel):
    """
    Classe para representar a temperatura da caldeira.
    """
    def __init__(self, min_value, max_value):
        super().__init__(min_value, max_value, ['ba', 'me', 'al'])

        
class VariavelVolume(Variavel):
    """
    Classe para representar o volume da caldeira.
    """
    def __init__(self, min_value, max_value):
        super().__init__(min_value, max_value, ['pe', 'me', 'gr'])
    

pressure_rules = {'pe': {'ba': 'ba', 'me': 'ba', 'al': 'me'},
                   'me': {'ba': 'ba', 'me': 'me', 'al': 'al'},
                   'gr': {'ba': 'me', 'me': 'al', 'al': 'al'}}


def get_pressure_fuzzy(volume, temperature):
    """
    Função para calcular a pressão com base no volume e temperatura.
    :param volume: volume do recipiente
    :param temperature: temperatura do recipiente
    :return: pressão do recipiente
    """
    try:
        return pressure_rules[volume][temperature]
    except KeyError:
        raise ValueError("Volume ou temperatura não reconhecidos.\n" \
        "Para volume, use 'pe' para pequeno, 'me' para médio, 'gr' para grande.\n" \
        "Para temperatura, use 'baixa', 'média', 'alta' para temperatura.")

def agregacao(variavel_temperatura, variavel_volume):
    pontos_discretizacao_temperatura = variavel_temperatura.pontos_discretizacao
    pontos_discretizacao_volume = variavel_volume.pontos_discretizacao

    # agregação é a união dos conjuntos fuzzy
    # o que significa que a agregação é o máximo entre os dois conjuntos
    # e o resultado é um novo conjunto fuzzy
    pertinencias_temperatura = [variavel_temperatura.fuzzificar_variavel(temperatura) for temperatura in pontos_discretizacao_temperatura]
    pertinencias_volume = [variavel_volume.fuzzificar_variavel(volume) for volume in pontos_discretizacao_volume]

if __name__ == '__main__':
    temperatura = 800
    volume = 11

    variavel_temperatura = VariavelTemperatura(800, 1200)
    variavel_volume = VariavelVolume(2, 12)

  
    temperatura_fuzzificada = variavel_temperatura.fuzzificar_variavel(temperatura)
    volume_fuzzificado = variavel_volume.fuzzificar_variavel(volume)

    inferencia_temperatura = max(temperatura_fuzzificada, key=temperatura_fuzzificada.get)
    inferencia_volume = max(volume_fuzzificado, key=volume_fuzzificado.get)

    #fazer inferencia de pressao
    #inferencia_pressao = min(temperatura_fuzzificada[inferencia_temperatura], volume_fuzzificado[inferencia_volume])

    # Chama a função para calcular a pressão
    inferencia_pressao = get_pressure_fuzzy(inferencia_volume, inferencia_temperatura)
    print(f"Pressão: {inferencia_pressao}")
