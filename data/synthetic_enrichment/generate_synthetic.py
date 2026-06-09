"""
Geração de Camada Sintética de Experimentação Adaptativa
=========================================================
Gera três arquivos que representam a camada de experimentação
sobre o dataset Bank Personal Loan Modelling:

1. offer_catalog.csv     — catálogo de braços/ofertas disponíveis
2. offer_events.csv      — eventos de impressão e decisão simulados
3. delayed_rewards.csv   — recompensas com horizonte temporal simulado

Semente aleatória controlada: 42
"""

import pandas as pd
import numpy as np
import os
from datetime import datetime, timedelta

np.random.seed(42)

OUTPUT_DIR = 'data/synthetic_enrichment'
os.makedirs(OUTPUT_DIR, exist_ok=True)

# ================================================================
# 1. OFFER CATALOG — catálogo de braços disponíveis
# ================================================================
# Define as ações que o bandit pode tomar.
# No projeto atual usamos 2 braços (mostrar/não mostrar),
# mas documentamos variações de mensagem para enriquecer o experimento.

print("Gerando offer_catalog.csv...")

offer_catalog = pd.DataFrame({
    'offer_id': [0, 1, 2, 3],
    'offer_name': [
        'no_offer',
        'banner_loan_standard',
        'banner_loan_urgency',
        'banner_loan_benefit'
    ],
    'offer_type': [
        'control',
        'banner',
        'banner',
        'banner'
    ],
    'message': [
        'Nenhuma oferta exibida',
        'Crédito pessoal com as melhores taxas. Simule agora.',
        'Oferta por tempo limitado: empréstimo pessoal com taxa especial.',
        'Realize seus planos com crédito pessoal sem burocracia.'
    ],
    'channel': [
        'none',
        'app',
        'app',
        'app'
    ],
    'arm_id': [0, 1, 1, 1],
    'active': [True, True, True, True],
    'created_at': ['2024-01-01'] * 4
})

offer_catalog.to_csv(f'{OUTPUT_DIR}/offer_catalog.csv', index=False)
print(f"  offer_catalog.csv: {len(offer_catalog)} ofertas")

# ================================================================
# 2. OFFER EVENTS — eventos de impressão e decisão simulados
# ================================================================
# Simula 5000 interações de clientes com o sistema,
# representando o log de decisões do bandit em produção.

print("Gerando offer_events.csv...")

# Carrega base processada para usar perfis reais
df_base = pd.read_csv('data/processed/bank_loan_processed.csv')

# Aplica filtro de suitability
def elegivel(row):
    if row['Age'] < 21:
        return False, 'idade_abaixo_21'
    if row['Income'] < 25:
        return False, 'renda_abaixo_minimo'
    if row['CreditCard'] == 0 and row['CD Account'] == 0 and row['Securities Account'] == 0:
        return False, 'sem_relacionamento_bancario'
    return True, None

# Gera eventos simulando clientes chegando ao sistema
n_events = 5000
start_date = datetime(2024, 1, 1)

events = []
for i in range(n_events):
    # Sorteia um cliente da base
    cliente = df_base.sample(1, random_state=i).iloc[0]

    # Verifica suitability
    is_elegivel, motivo_bloqueio = elegivel(cliente)

    # Simula decisão do bandit (EpsilonGreedy epsilon=0.2)
    if not is_elegivel:
        arm_shown = 0
        offer_shown = 'no_offer'
        decision_type = 'blocked'
    else:
        # 80% explotação, 20% exploração
        if np.random.random() < 0.2:
            arm_shown = np.random.choice([0, 1])
            decision_type = 'exploration'
        else:
            arm_shown = 1  # bandit aprendeu que mostrar é melhor
            decision_type = 'exploitation'
        offer_shown = 'no_offer' if arm_shown == 0 else 'banner_loan_standard'

    # Simula resultado (verdade oculta)
    if arm_shown == 1:
        if cliente['Income'] > 150 and cliente['Family'] >= 4:
            converted = np.random.choice([1, 0], p=[0.80, 0.20])
        elif cliente['Income'] > 100 and cliente['CD Account'] == 1:
            converted = np.random.choice([1, 0], p=[0.40, 0.60])
        else:
            converted = np.random.choice([1, 0], p=[0.12, 0.88])
    else:
        converted = 0

    # Calcula recompensa
    if arm_shown == 1 and converted == 1:
        reward = 1.0
    elif arm_shown == 1 and converted == 0:
        reward = -0.01
    else:
        reward = 0.0

    # Timestamp simulado
    event_time = start_date + timedelta(
        days=i // 20,
        hours=np.random.randint(8, 22),
        minutes=np.random.randint(0, 60)
    )

    events.append({
        'event_id': i + 1,
        'timestamp': event_time.isoformat(),
        'client_age': int(cliente['Age']),
        'client_income': int(cliente['Income']),
        'client_family': int(cliente['Family']),
        'client_education': int(cliente['Education']),
        'client_experience': int(cliente['Experience']),
        'client_securities_account': int(cliente['Securities Account']),
        'client_cd_account': int(cliente['CD Account']),
        'client_online': int(cliente['Online']),
        'client_credit_card': int(cliente['CreditCard']),
        'passed_suitability': is_elegivel,
        'suitability_block_reason': motivo_bloqueio,
        'arm_shown': arm_shown,
        'offer_shown': offer_shown,
        'decision_type': decision_type,
        'converted': converted,
        'immediate_reward': reward,
        'delayed_reward_available': False  # será preenchido no delayed_rewards
    })

df_events = pd.DataFrame(events)
df_events.to_csv(f'{OUTPUT_DIR}/offer_events.csv', index=False)
print(f"  offer_events.csv: {len(df_events)} eventos")

# Estatísticas dos eventos
elegíveis = df_events[df_events['passed_suitability'] == True]
print(f"  Clientes elegíveis: {len(elegíveis)} ({len(elegíveis)/len(df_events)*100:.1f}%)")
print(f"  Clientes bloqueados: {len(df_events) - len(elegíveis)}")
print(f"  Banner exibido: {(df_events['arm_shown'] == 1).sum()}")
print(f"  Conversões: {df_events['converted'].sum()}")
print(f"  Recompensa total: {df_events['immediate_reward'].sum():.1f}")

# ================================================================
# 3. DELAYED REWARDS — recompensas com horizonte temporal
# ================================================================
# Simula recompensas atrasadas: algumas conversões só são confirmadas
# dias depois da interação (ex: cliente clicou mas contratou depois).

print("Gerando delayed_rewards.csv...")

# Seleciona eventos onde houve exibição do banner
eventos_com_banner = df_events[df_events['arm_shown'] == 1].copy()

delayed_records = []
for _, evento in eventos_com_banner.iterrows():
    # 15% dos eventos com banner têm recompensa atrasada
    has_delayed = np.random.random() < 0.15

    if has_delayed:
        # Delay entre 1 e 7 dias
        delay_days = np.random.randint(1, 8)
        event_time = datetime.fromisoformat(evento['timestamp'])
        reward_time = event_time + timedelta(days=delay_days)

        # Recompensa atrasada pode ser conversão tardia
        # (cliente que não converteu imediatamente mas converteu depois)
        if evento['converted'] == 0:
            # 8% de chance de converter com delay
            delayed_converted = np.random.choice([1, 0], p=[0.08, 0.92])
        else:
            delayed_converted = 0  # já converteu imediatamente

        delayed_reward = 1.0 if delayed_converted == 1 else 0.0

        delayed_records.append({
            'event_id': int(evento['event_id']),
            'original_timestamp': evento['timestamp'],
            'reward_timestamp': reward_time.isoformat(),
            'delay_days': delay_days,
            'immediate_reward': evento['immediate_reward'],
            'delayed_converted': delayed_converted,
            'delayed_reward': delayed_reward,
            'total_reward': evento['immediate_reward'] + delayed_reward,
            'reward_type': 'delayed_conversion' if delayed_converted == 1 else 'no_additional_reward'
        })

df_delayed = pd.DataFrame(delayed_records)
df_delayed.to_csv(f'{OUTPUT_DIR}/delayed_rewards.csv', index=False)
print(f"  delayed_rewards.csv: {len(df_delayed)} registros")
print(f"  Conversões tardias: {df_delayed['delayed_converted'].sum()}")
print(f"  Recompensa adicional total: {df_delayed['delayed_reward'].sum():.1f}")

print("\nEnriquecimento sintético concluído com sucesso.")
print(f"Arquivos salvos em {OUTPUT_DIR}/")
