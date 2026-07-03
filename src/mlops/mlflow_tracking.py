"""
MLflow Tracking — Rastreio de Experimentos
==========================================
Registra experimentos do bandit no MLflow para
rastreabilidade, comparação e auditoria de modelos.

Instalação:
    pip install mlflow

Execução:
    cd /home/felipedeoliveiragoncalves/PycharmProjects/lastech
    python src/mlops/mlflow_tracking.py

Visualizar experimentos:
    mlflow ui
    Acesse: http://localhost:5000
"""

import sys
import os
import numpy as np
import pandas as pd

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

try:
    import mlflow
    import mlflow.sklearn
    MLFLOW_AVAILABLE = True
except ImportError:
    MLFLOW_AVAILABLE = False
    print("MLflow não instalado. Execute: pip install mlflow")

from modelo_mab import bandit, calcular_recompensa, verificar_suitability


# ================================================================
# CONFIGURAÇÃO DO MLFLOW
# ================================================================

EXPERIMENT_NAME = "datathon-7mlet-bandit"
MLFLOW_TRACKING_URI = "sqlite:///mlflow.db"  # local; em Azure: Azure ML workspace URI

def configurar_mlflow():
    if not MLFLOW_AVAILABLE:
        return False
    mlflow.set_tracking_uri(MLFLOW_TRACKING_URI)
    mlflow.set_experiment(EXPERIMENT_NAME)
    print(f"MLflow configurado — experimento: {EXPERIMENT_NAME}")
    return True


# ================================================================
# SIMULAÇÃO PARA RASTREIO
# ================================================================

def simular_para_mlflow(n_clientes=1000, seed=42):
    """
    Executa simulação e retorna métricas para registro no MLflow.
    """
    np.random.seed(seed)

    def gerar_cliente():
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

    def verdade_oculta(cliente):
        if cliente['Income'] > 150 and cliente['Family'] >= 4:
            return np.random.choice([1, 0], p=[0.80, 0.20])
        if cliente['Income'] > 100 and cliente['CD Account'] == 1:
            return np.random.choice([1, 0], p=[0.40, 0.60])
        return np.random.choice([1, 0], p=[0.12, 0.88])

    recompensas = []
    conversoes = []
    exploracoes = 0
    bloqueados = 0
    total_mostrou = 0

    for _ in range(n_clientes):
        cliente = gerar_cliente()
        resultado_real = verdade_oculta(cliente)
        elegivel, _ = verificar_suitability(cliente)

        if not elegivel:
            bloqueados += 1
            recompensas.append(0.0)
            continue

        acao = bandit.predict()
        recompensa = calcular_recompensa(acao, resultado_real)

        if np.random.random() < 0.2:
            exploracoes += 1

        if acao == 1:
            total_mostrou += 1
            if resultado_real == 1:
                conversoes.append(1)
            else:
                conversoes.append(0)

        recompensas.append(recompensa)

        bandit.partial_fit(decisions=[acao], rewards=[recompensa])

    metricas = {
        'recompensa_total': sum(recompensas),
        'recompensa_media': np.mean(recompensas),
        'taxa_conversao': np.mean(conversoes) if conversoes else 0,
        'taxa_exploracao': exploracoes / max(n_clientes - bloqueados, 1),
        'taxa_bloqueio': bloqueados / n_clientes,
        'total_mostrou': total_mostrou,
        'total_bloqueados': bloqueados,
        'n_clientes': n_clientes,
    }

    return metricas, recompensas


# ================================================================
# REGISTRAR EXPERIMENTO NO MLFLOW
# ================================================================

def registrar_experimento(
    versao_politica="1.0",
    algoritmo="EpsilonGreedy",
    epsilon=0.2,
    n_clientes=1000,
    seed=42
):
    """
    Executa uma rodada de simulação e registra no MLflow.
    """
    if not MLFLOW_AVAILABLE:
        print("MLflow não disponível. Pulando registro.")
        return

    if not configurar_mlflow():
        return

    print(f"\nIniciando experimento — versão {versao_politica}...")

    metricas, recompensas = simular_para_mlflow(n_clientes, seed)

    with mlflow.start_run(run_name=f"bandit-v{versao_politica}"):

        # Parâmetros
        mlflow.log_param("versao_politica", versao_politica)
        mlflow.log_param("algoritmo", algoritmo)
        mlflow.log_param("epsilon", epsilon)
        mlflow.log_param("n_clientes", n_clientes)
        mlflow.log_param("seed", seed)
        mlflow.log_param("inicializacao", "balanceada_50_50")
        mlflow.log_param("recompensa_conversao", 1.0)
        mlflow.log_param("penalidade_sem_conversao", -0.01)

        # Métricas
        mlflow.log_metric("recompensa_total", metricas['recompensa_total'])
        mlflow.log_metric("recompensa_media", metricas['recompensa_media'])
        mlflow.log_metric("taxa_conversao", metricas['taxa_conversao'])
        mlflow.log_metric("taxa_exploracao", metricas['taxa_exploracao'])
        mlflow.log_metric("taxa_bloqueio", metricas['taxa_bloqueio'])
        mlflow.log_metric("total_mostrou", metricas['total_mostrou'])
        mlflow.log_metric("total_bloqueados", metricas['total_bloqueados'])

        # Recompensa acumulada ao longo do tempo (por bloco de 100)
        acumulado = 0
        for i, r in enumerate(recompensas):
            acumulado += r
            if (i + 1) % 100 == 0:
                mlflow.log_metric(
                    "recompensa_acumulada",
                    acumulado,
                    step=(i + 1) // 100
                )

        # Tags
        mlflow.set_tag("projeto", "datathon-7mlet")
        mlflow.set_tag("dataset", "bank-personal-loan")
        mlflow.set_tag("status", "staging")

        print(f"\nExperimento registrado no MLflow:")
        print(f"  Recompensa total  : {metricas['recompensa_total']:+.1f}")
        print(f"  Recompensa média  : {metricas['recompensa_media']:+.4f}")
        print(f"  Taxa de conversão : {metricas['taxa_conversao']:.2%}")
        print(f"  Taxa de exploração: {metricas['taxa_exploracao']:.2%}")
        print(f"  Taxa de bloqueio  : {metricas['taxa_bloqueio']:.2%}")
        print(f"\nPara visualizar: mlflow ui")
        print(f"Acesse: http://localhost:5000")

    return metricas


# ================================================================
# EXECUÇÃO
# ================================================================

if __name__ == '__main__':
    registrar_experimento(
        versao_politica="1.0",
        algoritmo="EpsilonGreedy",
        epsilon=0.2,
        n_clientes=1000,
        seed=42
    )
