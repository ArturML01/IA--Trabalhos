import random
import numpy as np

# ---------------------------------------------------------
# 1. BASE DE DADOS: SELEÇÕES, ESTÁDIOS E DISTÂNCIAS (CATAR 2022)
# ---------------------------------------------------------

GRUPOS = {
    "A": ["Catar", "Equador", "Senegal", "Holanda"],
    "B": ["Inglaterra", "Irã", "Estados Unidos", "País de Gales"],
    "C": ["Argentina", "Arábia Saudita", "México", "Polônia"],
    "D": ["França", "Austrália", "Dinamarca", "Tunísia"],
    "E": ["Espanha", "Costa Rica", "Alemanha", "Japão"],
    "F": ["Bélgica", "Canadá", "Marrocos", "Croácia"],
    "G": ["Brasil", "Sérvia", "Suíça", "Camarões"],
    "H": ["Portugal", "Gana", "Uruguai", "Coreia do Sul"]
}

SELECOES = [time for grupo in GRUPOS.values() for time in grupo]
NUM_SELECOES = len(SELECOES)

ESTADIOS = [
    "Lusail Iconic Stadium",     
    "Al Bayt Stadium (Al Khor)",  
    "Stadium 974 (Doha)",          
    "Al Thumama (Doha)",          
    "Education City (Rayyan)",    
    "Ahmad bin Ali (Rayyan)",     
    "Khalifa International",      
    "Al Janoub (Al Wakrah)"       
]

DISTANCIAS = np.array([
    # 0   1   2   3   4   5   6   7
    [ 0, 35, 20, 25, 22, 23, 21, 38],  # 0: Lusail
    [35,  0, 45, 50, 48, 50, 46, 65],  # 1: Al Bayt
    [20, 45,  0, 12, 18, 22, 14, 20],  # 2: Stadium 974
    [25, 50, 12,  0, 20, 24, 15, 12],  # 3: Al Thumama
    [22, 48, 18, 20,  0,  8,  9, 28],  # 4: Education City
    [23, 50, 22, 24,  8,  0, 10, 32],  # 5: Ahmad bin Ali
    [21, 46, 14, 15,  9, 10,  0, 25],  # 6: Khalifa Int.
    [38, 65, 20, 12, 28, 32, 25,  0]   # 7: Al Janoub
])

SEDES_MATA_MATA = {
    "Oitavas_1st": 1,  # Al Bayt 
    "Oitavas_2nd": 3,  # Al Thumama 
    "Quartas":     4,  # Education City
    "Semifinal":   6,  # Khalifa International
    "Final":       0   # Lusail
}


# ---------------------------------------------------------
# 2. GERAÇÃO DE INDIVÍDUOS E CÁLCULO DE DISTÂNCIA PONDERADA
# ---------------------------------------------------------

def criar_individuo():
    """
    Cria uma tabela onde cada grupo joga 3 rodadas na fase de grupos.
    Retorna um dicionário {nome_selecao: [estadio_rodada_1, estadio_rodada_2, estadio_rodada_3]}
    """
    tabela = {}
    for nome_grupo, times in GRUPOS.items():
        for time in times:
            tabela[time] = [random.randint(0, len(ESTADIOS) - 1) for _ in range(3)]
    return tabela

def calcular_distancia_time(estadios_fase_grupos):
    """
    Calcula o trajeto esperado considerando o funil de eliminação real do torneio:
    - 100.0% de chance de jogar a Fase de Grupos (32 seleções)
    -  50.0% de chance de ir para as Oitavas de Final (16 seleções)
    -  25.0% de chance de ir para as Quartas de Final (8 seleções)
    -  12.5% de chance de ir para a Semifinal (4 seleções)
    -   6.25% de chance de ir para a Final (2 seleções)
    """
    # 1. Fase de Grupos (2 deslocamentos garantidos para todas as 32 seleções)
    dist_grupos = (DISTANCIAS[estadios_fase_grupos[0]][estadios_fase_grupos[1]] +
                   DISTANCIAS[estadios_fase_grupos[1]][estadios_fase_grupos[2]])
    
    ultimo_estadio_grupo = estadios_fase_grupos[-1]
    
    # 2. Deslocamento até as Oitavas (P = 0.50)
    # Pondera 50% de chance de passar em 1º (Oitavas_1st) e 50% em 2º (Oitavas_2nd)
    dist_para_oitavas = 0.5 * DISTANCIAS[ultimo_estadio_grupo][SEDES_MATA_MATA["Oitavas_1st"]] + \
                        0.5 * DISTANCIAS[ultimo_estadio_grupo][SEDES_MATA_MATA["Oitavas_2nd"]]
    
    # 3. Deslocamento Oitavas -> Quartas (P = 0.25)
    dist_para_quartas = 0.5 * DISTANCIAS[SEDES_MATA_MATA["Oitavas_1st"]][SEDES_MATA_MATA["Quartas"]] + \
                        0.5 * DISTANCIAS[SEDES_MATA_MATA["Oitavas_2nd"]][SEDES_MATA_MATA["Quartas"]]
    
    # 4. Deslocamento Quartas -> Semifinal (P = 0.125)
    dist_para_semi = DISTANCIAS[SEDES_MATA_MATA["Quartas"]][SEDES_MATA_MATA["Semifinal"]]
    
    # 5. Deslocamento Semifinal -> Final (P = 0.0625)
    dist_para_final = DISTANCIAS[SEDES_MATA_MATA["Semifinal"]][SEDES_MATA_MATA["Final"]]
    
    # Somatório do Valor Esperado no Mata-Mata
    mata_mata_esperado = (0.5000 * dist_para_oitavas) + \
                         (0.2500 * dist_para_quartas) + \
                         (0.1250 * dist_para_semi) + \
                         (0.0625 * dist_para_final)
    
    return dist_grupos + mata_mata_esperado

def calcular_custo_total(individuo):
    """Soma a distância ponderada de todas as seleções com penalidades logísticas."""
    distancia_total = 0
    penalidade = 0
    
    for time, estadios in individuo.items():
        distancia_total += calcular_distancia_time(estadios)
        
    # Penalidade por sobrecarga de estádios (> 4 jogos na mesma rodada)
    for rodada in range(3):
        estadios_usados = [estadios[rodada] for estadios in individuo.values()]
        for e in set(estadios_usados):
            if estadios_usados.count(e) > 4:
                penalidade += 500
                
    return distancia_total + penalidade

# ---------------------------------------------------------
# 3. OPERADORES GENÉTICOS
# ---------------------------------------------------------

def selecao_torneio(populacao, k=3):
    competidores = random.sample(populacao, k)
    return min(competidores, key=calcular_custo_total)

def cruzamento(pai1, pai2):
    filho = {}
    grupos_chaves = list(GRUPOS.keys())
    ponto_corte = len(grupos_chaves) // 2  
    grupos_p1 = grupos_chaves[:ponto_corte]
    
    for nome_grupo, times in GRUPOS.items():
        for time in times:
            if nome_grupo in grupos_p1:
                filho[time] = list(pai1[time])
            else:
                filho[time] = list(pai2[time])
    return filho

def mutacao(individuo, taxa_mutacao=0.15):
    mutado = {time: list(estadios) for time, estadios in individuo.items()}
    for time in mutado:
        if random.random() < taxa_mutacao:
            rodada_alterada = random.randint(0, 2)
            mutado[time][rodada_alterada] = random.randint(0, len(ESTADIOS) - 1)
    return mutado


# ---------------------------------------------------------
# 4. EXECUÇÃO DO ALGORITMO GENÉTICO
# ---------------------------------------------------------

TAMANHO_POPULACAO = 100
GERACOES = 250

populacao = [criar_individuo() for _ in range(TAMANHO_POPULACAO)]

print("Otimizando tabela para as 32 Seleções (Funil Realista de Eliminação)...\n")

for gen in range(GERACOES):
    populacao.sort(key=calcular_custo_total)
    melhor_custo = calcular_custo_total(populacao[0])
    
    if (gen + 1) % 50 == 0 or gen == 0:
        print(f"Geração {gen+1:3d} | Menor Trajeto Esperado Total: {melhor_custo:.1f} km")
        
    proxima_gen = populacao[:5]  # Elitismo de 5%
    
    while len(proxima_gen) < TAMANHO_POPULACAO:
        p1 = selecao_torneio(populacao)
        p2 = selecao_torneio(populacao)
        filho = cruzamento(p1, p2)
        filho = mutacao(filho)
        proxima_gen.append(filho)
        
    populacao = proxima_gen

melhor_tabela = min(populacao, key=calcular_custo_total)
menor_distancia = calcular_custo_total(melhor_tabela)

# ---------------------------------------------------------
# 5. RESULTADOS
# ---------------------------------------------------------

print("\n" + "="*60)
print(f" TABELA OTIMIZADA PARA 32 SELEÇÕES (VALOR ESPERADO TOTAL: {menor_distancia:.1f} km)")
print("="*60)

for nome_grupo, times in GRUPOS.items():
    print(f"\n--- PROGRAMAÇÃO DO GRUPO {nome_grupo} (Fase de Grupos) ---")
    for time in times:
        estadios_nomes = [ESTADIOS[i] for i in melhor_tabela[time]]
        print(f"  {time:15s} -> R1: {estadios_nomes[0]} | R2: {estadios_nomes[1]} | R3: {estadios_nomes[2]}")

print("\n--- SEDES DEFINIDAS PARA O MATA-MATA ---")
print(f"  Oitavas (Se 1º lugar): {ESTADIOS[SEDES_MATA_MATA['Oitavas_1st']]}")
print(f"  Oitavas (Se 2º lugar): {ESTADIOS[SEDES_MATA_MATA['Oitavas_2nd']]}")
print(f"  Quartas de Final:      {ESTADIOS[SEDES_MATA_MATA['Quartas']]}")
print(f"  Semifinal:             {ESTADIOS[SEDES_MATA_MATA['Semifinal']]}")
print(f"  Grande Final:          {ESTADIOS[SEDES_MATA_MATA['Final']]}")