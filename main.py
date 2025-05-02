import os
import numpy as np

regras_pressao = {
    ('pe', 'ba'): 'ba', ('pe', 'me'): 'ba', ('pe', 'al'): 'me',
    ('me', 'ba'): 'ba', ('me', 'me'): 'me', ('me', 'al'): 'al',
    ('gr', 'ba'): 'me', ('gr', 'me'): 'al', ('gr', 'al'): 'al'
}

def triangular(x, a, b, c):
    x = np.asarray(x, float)
    # fora de [a,c] dá <0 ou <0, e o np.maximum zera.
    return np.maximum(0, np.minimum((x - a)/(b - a), (c - x)/(c - b)))

def trapezio_ascendente(x, a, b, c):
    x = np.asarray(x, float)
    # <a => <0 ⇒ clip→0 ; entre a e b cresce de 0→1 ; >b => >1 ⇒ clip→1
    return np.clip((x - a)/(b - a), 0, 1)

def trapezio_descendente(x, a, b, c):
    x = np.asarray(x, float)
    # <b ⇒ >1 ⇒ clip→1 ; entre b e c decresce ; >c ⇒ <0 ⇒ clip→0
    return np.clip((c - x)/(c - b), 0, 1)

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
        """
        Inicializa a variável com os valores mínimos e máximos, conjunto de termos e pontos de discretização.
        :param min_value: valor mínimo
        :param max_value: valor máximo
        :param conjunto_termos: conjunto de termos
        :param pontos_discretizacao: pontos de discretização
        :param fracao: fração do universo de discurso
        """
        self.min_value = min_value
        self.max_value = max_value
        self.conjunto_termos = conjunto_termos
        self.pontos_discretizacao = np.linspace(min_value, max_value, 500)
        self.fracao = (max_value - min_value) / 4


    def _verificar_se_pertence_universo_discurso(self, input):
        """
        Função para verificar se o valor de entrada pertence ao universo de discurso.
        :param input: valor de entrada
        :return: True se pertence, False caso contrário
        """
        return self.min_value <= input <= self.max_value
    

    def fuzzificar_variavel(self, input):
        if not self._verificar_se_pertence_universo_discurso(input):
            raise ValueError(f"Valor de entrada {input} não pertence ao universo de discurso.")
        """
        Função para fuzzificar a variável.
        :param input: valor de entrada
        :return: dicionário com os valores de pertinência
        """
        return {self.conjunto_termos[0]: trapezio_descendente(input, self.min_value + self.fracao, self.min_value + self.fracao*2, self.min_value + self.fracao*3),
                self.conjunto_termos[1]: triangular(input, self.min_value + self.fracao*2, self.min_value + self.fracao*3, self.min_value + self.fracao*4),
                self.conjunto_termos[2]: trapezio_ascendente(input, self.min_value + self.fracao*3, self.min_value + self.fracao*4, self.min_value + self.fracao*5)}
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
    

class VariavelPressao(Variavel):
    """
    Classe para representar a pressão da caldeira.
    """
    def __init__(self, min_value, max_value):
        super().__init__(min_value, max_value, ['ba', 'me', 'al'])


def get_pressure_fuzzy(volume, temperature):
    """
    Função para calcular a pressão com base no volume e temperatura.
    :param volume: volume do recipiente
    :param temperature: temperatura do recipiente
    :return: pressão do recipiente
    """
    try:
        return regras_pressao[volume][temperature]
    except KeyError:
        raise ValueError("Volume ou temperatura não reconhecidos.\n" \
        "Para volume, use 'pe' para pequeno, 'me' para médio, 'gr' para grande.\n" \
        "Para temperatura, use 'baixa', 'média', 'alta' para temperatura.")

def obter_ativacao(vf, tf, regras):
    """
    Função para obter o corte da ativação da regra para cada termo.
    :param vf: volume fuzzificado
    :param tf: temperatura fuzzificada
    :param regras: regras de inferência
    :return: ativação da regra
    """
    ativacao_pressao = {'ba': 0.0, 'me': 0.0, 'al': 0.0}
    for termo_volume, pertinencia_volume in vf.items():
        if pertinencia_volume == 0: continue
        for termo_temperatura, pertinencia_temperatura in tf.items():
            if pertinencia_temperatura == 0: continue
            saida = regras[(termo_volume, termo_temperatura)]
            ativacao_pressao[saida] = max(ativacao_pressao[saida], min(pertinencia_volume, pertinencia_temperatura))
    return ativacao_pressao

def agregacao(ativacao, pertinencias_ba, pertinencias_me, pertinencias_al):
    """
    Função para agregar a ativação da regra.
    :param ativacao: ativação da regra
    :return: valor agregado
    """
    corte_ba = np.minimum(ativacao['ba'], pertinencias_ba)
    corte_me = np.minimum(ativacao['me'], pertinencias_me)
    corte_al = np.minimum(ativacao['al'], pertinencias_al)

    return np.maximum.reduce([corte_ba, corte_me, corte_al])#, corte_ba, corte_me, corte_al # reduz a lista de arrays a um único array, pegando o máximo entre eles
    
def defuzzificacao_centro_area(pontos_discretizacao, pertinencias_agregadas):
    """
    Função para defuzzificar a variável pelo método do centro de área.
    :param pontos_discretizacao: pontos de discretização
    :param pertinencias_agregadas: pertinências agregadas
    :return: valor defuzzificado
    """
    num = np.sum(pontos_discretizacao * pertinencias_agregadas)
    den = np.sum(pertinencias_agregadas)
    return num / den if den != 0 else 0

def defuzzificacao_media_maximos(pontos_discretizacao, pertinencias_agregadas):
    """
    Função para defuzzificar a variável pelo método da média dos máximos.
    :param pontos_discretizacao: pontos de discretização
    :param pertinencias_agregadas: pertinências agregadas
    :return: valor defuzzificado
    """
    maximo = np.max(pertinencias_agregadas)
    indices_maximos = np.where(pertinencias_agregadas == maximo)[0]
    return np.mean(pontos_discretizacao[indices_maximos]) if len(indices_maximos) > 0 else 0

def defuzzificacao_primeiro_maximo(pontos_discretizacao, pertinencias_agregadas):
    """
    Função para defuzzificar a variável pelo método do primeiro máximo.
    :param pontos_discretizacao: pontos de discretização
    :param pertinencias_agregadas: pertinências agregadas
    :return: valor defuzzificado
    """
    maximo = np.max(pertinencias_agregadas)
    indice_maximo = np.argmax(pertinencias_agregadas)
    return pontos_discretizacao[indice_maximo] if maximo > 0 else 0

if __name__ == '__main__':
    temperatura = 1122
    volume = 5.2
    nome_fig = 'ex2_e'

    variavel_temperatura = VariavelTemperatura(800, 1200)
    variavel_volume = VariavelVolume(2, 12)
    variavel_pressao = VariavelPressao(4, 12)

    pontos_temperatura = variavel_temperatura.pontos_discretizacao
    pontos_volume = variavel_volume.pontos_discretizacao
    pontos_pressao = variavel_pressao.pontos_discretizacao

    pertinencias_temperatura_ba = trapezio_descendente(pontos_temperatura, 800, 900, 1000)
    pertinencias_temperatura_me = triangular(pontos_temperatura, 900, 1000, 1100)
    pertinencias_temperatura_al = trapezio_ascendente(pontos_temperatura, 1000, 1100, 1200)

    pertinencias_volume_pe = trapezio_descendente(pontos_volume, 2, 4, 6)
    pertinencias_volume_me = triangular(pontos_volume, 4, 6, 8)
    pertinencias_volume_gr = trapezio_ascendente(pontos_volume, 6, 8, 12)

    pertinencias_pressao_ba = trapezio_descendente(pontos_pressao, 4, 5, 8)
    pertinencias_pressao_me = triangular(pontos_pressao, 6, 8, 10)
    pertinencias_pressao_al = trapezio_ascendente(pontos_pressao, 8, 11, 12)

    pertinencia_temperatura = variavel_temperatura.fuzzificar_variavel(temperatura)
    pertinencia_volume = variavel_volume.fuzzificar_variavel(volume)

    ativacao = obter_ativacao(pertinencia_volume, pertinencia_temperatura, regras_pressao)
    pertinencias_agregadas = agregacao(ativacao, pertinencias_pressao_ba, pertinencias_pressao_me, pertinencias_pressao_al)
   
    pressao_cda = defuzzificacao_centro_area(pontos_pressao, pertinencias_agregadas)
    pressao_mdm = defuzzificacao_media_maximos(pontos_pressao, pertinencias_agregadas)
    pressao_mpm = defuzzificacao_primeiro_maximo(pontos_pressao, pertinencias_agregadas)

    print('Ativação de temperatura nos conjuntos de termos:', pertinencia_temperatura)
    print('Ativação de volume nos conjuntos de termos:', pertinencia_volume)

    print(f"Pressão CDA: {pressao_cda:.2f} atm")
    print(f"Pressão MDM: {pressao_mdm:.2f} atm")
    print(f"Pressão MPM: {pressao_mpm:.2f} atm")
    print('Ativação de pressão nos conjuntos de termos:', ativacao)

    # plot
    import matplotlib.pyplot as plt

    plt.plot(pontos_pressao, pertinencias_pressao_ba)
    plt.plot(pontos_pressao, pertinencias_pressao_me)
    plt.plot(pontos_pressao, pertinencias_pressao_al)
    plt.plot(pontos_pressao, pertinencias_agregadas)
    plt.fill_between(pontos_pressao, 0, pertinencias_agregadas, alpha=0.2, color='red')
    plt.legend(['baixa', 'média', 'alta', 'agregada'])
    plt.title('Agregação Final')
    plt.xlabel('Pressão')
    plt.ylabel('Pertinência')

    # salvar
    os.makedirs('imagens/', exist_ok=True)
    plt.savefig(f'imagens/{nome_fig}.png')
   

    


    
  
