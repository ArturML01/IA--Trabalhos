import random
import numpy as np

# ---------------------------------------------------------
# 1. BASE DE DADOS: SELEÇÕES, ESTÁDIOS E DISTÂNCIAS (CATAR 2022)
# ---------------------------------------------------------

# Todas as 32 Seleções divididas em 8 Grupos (A ate H)
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
    "Lusail Iconic Stadium",      # 0
    "Al Bayt Stadium (Al Khor)",  # 1
    "Stadium 974 (Doha)",          # 2
    "Al Thumama (Doha)",          # 3
    "Education City (Rayyan)",    # 4
    "Ahmad bin Ali (Rayyan)",     # 5
    "Khalifa International",      # 6
    "Al Janoub (Al Wakrah)"       # 7
]

# Matriz de distâncias (km) entre os estádios do Catar
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

# Atribuição fixa dos estádios para a fase de Mata-Mata
SEDES_MATA_MATA = {
    "Oitavas_1st": 1,  # Al Bayt (Ex: 1º do Grupo)
    "Oitavas_2nd": 3,  # Al Thumama (Ex: 2º do Grupo)
    "Quartas":     4,  # Education City
    "Semifinal":   6,  # Khalifa International
    "Final":       0   # Lusail
}


# ---------------------------------------------------------
# 2. GERAÇÃO DE INDIVÍDUOS E CÁLCULO DE DISTÂNCIA
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
    Calcula o trajeto da Fase de Grupos + Média Esperada do Mata-Mata (50% 1º / 50% 2º).
    """
    # 1. Distância na Fase de Grupos (3 jogos)
    dist_grupos = (DISTANCIAS[estadios_fase_grupos[0]][estadios_fase_grupos[1]] +
                   DISTANCIAS[estadios_fase_grupos[1]][estadios_fase_grupos[2]])
    
    ultimo_estadio_grupo = estadios_fase_grupos[-1]
    
    # 2. Trajeto se classificar em 1º lugar no grupo:
    caminho_1st = [ultimo_estadio_grupo, SEDES_MATA_MATA["Oitavas_1st"],
                   SEDES_MATA_MATA["Quartas"], SEDES_MATA_MATA["Semifinal"], SEDES_MATA_MATA["Final"]]
    dist_1st = sum(DISTANCIAS[caminho_1st[i]][caminho_1st[i+1]] for i in range(len(caminho_1st)-1))
    
    # 3. Trajeto se classificar em 2º lugar no grupo:
    caminho_2nd = [ultimo_estadio_grupo, SEDES_MATA_MATA["Oitavas_2nd"],
                   SEDES_MATA_MATA["Quartas"], SEDES_MATA_MATA["Semifinal"], SEDES_MATA_MATA["Final"]]
    dist_2nd = sum(DISTANCIAS[caminho_2nd[i]][caminho_2nd[i+1]] for i in range(len(caminho_2nd)-1))
    
    return dist_grupos + (0.5 * dist_1st + 0.5 * dist_2nd)

def calcular_custo_total(individuo):
    """Soma a distância de todas as seleções no campeonato com penalidades logísticas."""
    distancia_total = 0
    penalidade = 0
    
    # 1. Soma trajetos de cada time
    for time, estadios in individuo.items():
        distancia_total += calcular_distancia_time(estadios)
        
    # 2. Penalidade por sobrecarga de estádios na mesma rodada da fase de grupos
    # 32 times (16 jogos por rodada) e 8 estádios, a média perfeita é 2 jogos/estádio.
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
    """Combina alocações de estádios: metade dos grupos do Pai 1, metade do Pai 2."""
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
    """Sorteia e altera o estádio de uma das rodadas da fase de grupos para uma seleção."""
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

print("Otimizando tabela para as 32 Seleções (Fase de Grupos + Mata-Mata)...\n")

for gen in range(GERACOES):
    populacao.sort(key=calcular_custo_total)
    melhor_custo = calcular_custo_total(populacao[0])
    
    if (gen + 1) % 50 == 0 or gen == 0:
        print(f"Geração {gen+1:3d} | Menor Trajeto Médio Total: {melhor_custo:.1f} km")
        
    proxima_gen = populacao[:5]  
    
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
# 5. RESULTADOS DETALHADOS
# ---------------------------------------------------------

print("\n" + "="*60)
print(f" TABELA OTIMIZADA PARA 32 SELEÇÕES (MÉDIA TOTAL: {menor_distancia:.1f} km)")
print("="*60)

for nome_grupo, times in GRUPOS.items():
    print(f"\n--- PROGRAMAÇÃO DO GRUPO {nome_grupo} (Fase de Grupos) ---")
    for time in times:
        estadios_nomes = [ESTADIOS[i] for i in melhor_tabela[time]]
        print(f"  {time:15s} -> R1: {estadios_nomes[0]} | R2: {estadios_nomes[1]} | R3: {estadios_nomes[2]}")

print("\n--- SEDES DEFINIDAS PARA O MATA-MATA (A Partir do 3º Jogo) ---")
print(f"  Oitavas (Se 1º lugar): {ESTADIOS[SEDES_MATA_MATA['Oitavas_1st']]}")
print(f"  Oitavas (Se 2º lugar): {ESTADIOS[SEDES_MATA_MATA['Oitavas_2nd']]}")
print(f"  Quartas de Final:      {ESTADIOS[SEDES_MATA_MATA['Quartas']]}")
print(f"  Semifinal:             {ESTADIOS[SEDES_MATA_MATA['Semifinal']]}")
print(f"  Grande Final:          {ESTADIOS[SEDES_MATA_MATA['Final']]}")