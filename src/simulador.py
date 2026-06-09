"""
Simula clientes chegando ao sistema e mede se o bandit aprende.
Importa o bandit já inicializado do 02_bandit.py
"""

import pandas as pd
import numpy as np
from modelo_mab import bandit, tomar_decisao, salvar_log,verificar_suitability,calcular_recompensa
import xgboost as xb

np.random.seed(42)

# =============================================================
# PARTE 1 — GERADOR DE CLIENTES SINTÉTICOS
# =============================================================
# Cria clientes falsos com perfis variados.
# Usamos as mesmas 9 variáveis do seu modelo.

def gerar_cliente():
    """
    Gera um cliente sintético com perfil aleatório.
    Os ranges são baseados nos dados reais do seu dataset.
    """
    return {
        'Age':                np.random.randint(20, 70),
        'Experience':         np.random.randint(0, 40),
        'Income':             np.random.randint(10, 200),
        'Family':             np.random.randint(1, 5),
        'Education':          np.random.randint(1, 4),
        'Securities Account': np.random.randint(0, 2),
        'CD Account':         np.random.randint(0, 2),
        'Online':             np.random.randint(0, 2),
        'CreditCard':         np.random.randint(0, 2),
    }

# =============================================================
# PARTE 2 — VERDADE OCULTA (o que o cliente realmente faria)
# =============================================================
# Você define isso — é a "realidade" que o bandit precisa aprender.
# No mundo real essa função não existe; aqui ela simula o comportamento.

def verdade_oculta(cliente):
    # Perfil de alta propensão
    if cliente['Income'] > 150 and cliente['Family'] >= 4:
        return np.random.choice([1, 0], p=[0.80, 0.20])

    # Perfil de média propensão
    if cliente['Income'] > 100 and cliente['CD Account'] == 1:
        return np.random.choice([1, 0], p=[0.40, 0.60])

    # Perfil de baixa propensão — mas não zero
    return np.random.choice([1, 0], p=[0.12, 0.88])

# =============================================================
# PARTE 3 — RODAR A SIMULAÇÃO
# =============================================================

def rodar_simulacao(n_clientes=1000):
    """
    Simula n_clientes chegando ao sistema um a um.
    Registra tudo no log de auditoria.
    """
    print(f"Iniciando simulação com {n_clientes} clientes...\n")

    for i in range(n_clientes):
        cliente = gerar_cliente()

        # tomar_decisao já cuida de tudo:
        # suitability → bandit → log → aprendizado
        tomar_decisao(
            cliente=cliente,
            bandit=bandit,
            observar_recompensa=verdade_oculta
        )

        # Progresso a cada 100 clientes
        if (i + 1) % 100 == 0:
            print(f"  {i+1} clientes processados...")

    print("\nSimulação concluída.")
    df_log = salvar_log('log_auditoria.csv')
    return df_log


# =============================================================
# PARTE 4 — MÉTRICAS BÁSICAS
# =============================================================
# Mostra se o bandit foi melhorando ao longo do tempo.

def avaliar_resultado(df_log):
    """
    Divide o log em blocos de 100 e mostra a recompensa média
    de cada bloco. Se o bandit aprendeu, a recompensa deve
    crescer ao longo do tempo.
    """
    elegíveis = df_log[df_log['passou_suitability'] == True].copy()
    elegíveis = elegíveis.reset_index(drop=True)

    tamanho_bloco = 100
    print("\nEvolução da recompensa média por bloco de 100 clientes:")
    print("-" * 45)

    for inicio in range(0, len(elegíveis), tamanho_bloco):
        bloco = elegíveis.iloc[inicio:inicio + tamanho_bloco]
        recompensa_media = bloco['recompensa'].mean()
        bloco_num = (inicio // tamanho_bloco) + 1
        barra = "█" * int(recompensa_media * 20)
        print(f"  Bloco {bloco_num:>2}: {recompensa_media:+.3f}  {barra}")

    print("-" * 45)
    total_mostrou   = (elegíveis['acao'] == 1).sum()
    total_bloqueado = (df_log['passou_suitability'] == False).sum()
    total_explorou  = (elegíveis['tipo_decisao'] == 'exploracao').sum()

    print(f"\n  Total de clientes simulados : {len(df_log)}")
    print(f"  Bloqueados pelo suitability : {total_bloqueado}")
    print(f"  Banner mostrado             : {total_mostrou}")
    print(f"  Decisões de exploração      : {total_explorou}")

np.random.seed(42)

# =============================================================
# PARTE 1 — FUNÇÕES DE CADA BASELINE
# =============================================================

modelo_xgb = xb.XGBClassifier()
modelo_xgb.load_model('modelo_xgboost.json')

def baseline_mostrar_sempre(cliente):
    elegivel, _ = verificar_suitability(cliente)
    return 1 if elegivel else 0

def baseline_nao_mostrar(cliente):
    return 0

def baseline_aleatorio(cliente):
    elegivel, _ = verificar_suitability(cliente)
    if not elegivel:
        return 0
    return np.random.choice([0, 1])

def baseline_xgboost_fixo(cliente, threshold=0.5):
    elegivel, _ = verificar_suitability(cliente)
    if not elegivel:
        return 0
    contexto = pd.DataFrame([cliente])
    prob = modelo_xgb.predict_proba(contexto)[0][1]
    return 1 if prob >= threshold else 0


# =============================================================
# PARTE 2 — FUNÇÃO GENÉRICA DE SIMULAÇÃO
# =============================================================

def simular_estrategia(nome, funcao_decisao, n_clientes=1000):
    """
    Roda uma estratégia qualquer por n_clientes e retorna
    a lista de recompensas acumuladas ao longo do tempo.
    """
    recompensas = []
    acumulado   = []
    soma        = 0

    for _ in range(n_clientes):
        cliente = gerar_cliente()
        acao    = funcao_decisao(cliente)
        resultado_real = verdade_oculta(cliente)
        recompensa     = calcular_recompensa(acao, resultado_real)

        soma += recompensa
        recompensas.append(recompensa)
        acumulado.append(soma)

    print(f"  {nome:<25} | Recompensa total: {soma:+.1f} | Média: {soma/n_clientes:+.4f}")
    return acumulado

def simular_bandit(n_clientes=1000):
    """
    Roda o bandit de forma comparável aos baselines:
    gera n_clientes, calcula recompensa para cada um.
    """
    acumulado = []
    soma      = 0

    for _ in range(n_clientes):
        cliente        = gerar_cliente()
        resultado_real = verdade_oculta(cliente)

        # verifica suitability manualmente para ter a ação
        elegivel, _ = verificar_suitability(cliente)
        if not elegivel:
            acao = 0
        else:
            contexto = pd.DataFrame([cliente])
            acao = bandit.predict(contexts=contexto)

            # aprendizado online
            recompensa_online = calcular_recompensa(acao, resultado_real)
            bandit.partial_fit(
                decisions=[acao],
                rewards=[recompensa_online]
            )

        # recompensa para comparação — mesma lógica dos baselines
        recompensa = calcular_recompensa(acao, resultado_real)
        soma += recompensa
        acumulado.append(soma)

    print(f"  {'Bandit (Thompson)':<25} | Recompensa total: {soma:+.1f} | Média: {soma/n_clientes:+.4f}")
    return acumulado


# =============================================================
# PARTE 3 — RODAR TUDO E COMPARAR
# =============================================================

def comparar_baselines(n_clientes=1000):
    print(f"\nComparando estratégias — {n_clientes} clientes cada\n")
    print("-" * 60)

    resultados = {}

    np.random.seed(100)
    resultados['Mostrar sempre'] = simular_estrategia(
        'Mostrar sempre', baseline_mostrar_sempre, n_clientes)

    np.random.seed(100)
    resultados['Não mostrar'] = simular_estrategia(
        'Não mostrar', baseline_nao_mostrar, n_clientes)

    np.random.seed(100)
    resultados['Aleatório'] = simular_estrategia(
        'Aleatório', baseline_aleatorio, n_clientes)

    np.random.seed(100)
    resultados['XGBoost fixo'] = simular_estrategia(
        'XGBoost fixo', baseline_xgboost_fixo, n_clientes)

    np.random.seed(100)
    resultados['Bandit'] = simular_bandit(n_clientes)

    print("-" * 60)

    df_resultado = pd.DataFrame(resultados)
    df_resultado.to_csv('comparacao_baselines.csv', index=False)
    print(f"\nResultados salvos em 'comparacao_baselines.csv'")

    return df_resultado


# =============================================================
# EXECUÇÃO
# =============================================================

if __name__ == '__main__':
    # Passo 7 — simulação e métricas básicas
    df_log = rodar_simulacao(n_clientes=5000)
    avaliar_resultado(df_log)

    # Passo 8 — comparação com baselines
    df = comparar_baselines(n_clientes=5000)