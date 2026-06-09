"""
2. Definir o contexto do bandit
Quais variáveis descrevem o cliente no momento da decisão? Provavelmente um subconjunto do que você já usou no XGBoost. Isso vira o "input" de cada rodada do bandit.

'Age', 'Experience', 'Income','Family','Education','Securities Account','CD Account', 'Online', 'CreditCard'

########################

3. Definir a recompensa
Decidir se é binária (converteu = 1, não converteu = 0) ou se você vai penalizar exibição sem retorno. Essa escolha muda o comportamento do modelo.


Mostrou o banner → cliente aceitou  = +1
Mostrou o banner → cliente recusou  = -0.1  (pequena penalidade)
Não mostrou o banner                =  0

########################

4. Implementar o filtro de suitability
A camada que roda antes do bandit e bloqueia clientes para quem o banner nunca pode ser mostrado. Regras simples, mas precisam existir.

Baseada em perfil
a) Idade < 21 anos

Baseadas em risco financeiro
b) Income < 25

Baseadas em relacionamento
c) CreditCard = 0, CD Account = 0, Securities Account = 0

########################

5. Implementar o decisor (bandit contextual)
O coração do sistema. Recebe o contexto, consulta o que aprendeu até agora, escolhe mostrar ou não — equilibrando exploração e explotação.


########################

"""

import pandas as pd
import numpy as np
from mabwiser.mab import MAB, LearningPolicy, NeighborhoodPolicy
import xgboost as xb
from datetime import datetime

# Carregar modelo XGBOOST

data = pd.read_csv('Bank_Personal_Loan_Modelling(1).csv')
df = data[['Age', 'Experience', 'Income','Family','Education','Securities Account',
       'CD Account', 'Online', 'CreditCard','Personal Loan']]
df = df[df['Experience']>=0]
X = df[['Age', 'Experience', 'Income','Family','Education','Securities Account',
       'CD Account', 'Online', 'CreditCard']]
y = df['Personal Loan']
modelo_xgb = xb.XGBClassifier()
modelo_xgb.load_model('modelo_xgboost.json')

# Aplicar filtro de suitability

def verificar_suitability(cliente):
    """
    Retorna (elegivel, motivo_bloqueio)
    """
    if cliente['Age'] < 21:
        return False, 'idade_abaixo_21'
    if cliente['Income'] < 25:
        return False, 'renda_abaixo_minimo'
    if (cliente['CreditCard'] == 0 and
        cliente['CD Account'] == 0 and
        cliente['Securities Account'] == 0):
        return False, 'sem_relacionamento_bancario'
    return True, None

# Filtrar na base de dados
mask_elegivel = X.apply(lambda c: verificar_suitability(c)[0], axis=1)
X_elegivel = X[mask_elegivel]
y_elegivel = y[mask_elegivel]

# Define a função ANTES de usar

def calcular_recompensa(decisao, resultado_real):
    if decisao == 1 and resultado_real == 1:
        return 1.0
    elif decisao == 1 and resultado_real == 0:
        return -0.01
    else:
        return 0.0

# Inicialização com histórico sintético
# Usa a mesma lógica de conversão da simulação (não o dataset real)
np.random.seed(42)
n_init = len(X_elegivel)
metade = n_init // 2

decisoes_historicas = [1] * metade + [0] * (n_init - metade)

# Gera recompensas simulando a verdade oculta para cada perfil
# Gera recompensas simulando a verdade oculta para cada perfil
recompensas_historicas = []
for d, (_, perfil) in zip(decisoes_historicas, X_elegivel.iterrows()):
    if d == 0:
        recompensas_historicas.append(0.0)
        continue
    income = perfil['Income']
    family = perfil['Family']
    cd     = perfil['CD Account']
    if income > 150 and family >= 4:
        r = np.random.choice([1, 0], p=[0.80, 0.20])
    elif income > 100 and cd == 1:
        r = np.random.choice([1, 0], p=[0.40, 0.60])
    else:
        r = np.random.choice([1, 0], p=[0.12, 0.88])
    recompensas_historicas.append(calcular_recompensa(d, r))

# =============================================================
# CRIAR E INICIALIZAR O BANDIT
# =============================================================

bandit = MAB(
    arms=[0, 1],
    learning_policy=LearningPolicy.EpsilonGreedy(epsilon=0.2)
)

bandit.fit(
    decisions=decisoes_historicas,
    rewards=recompensas_historicas
)

print('BANDIT INICIALIZADO COM HISTÓRICO OFFLINE')
print(f'Clientes usados na inicialização: {len(X_elegivel)}')
print(f'Clientes removidos pelo suitability: {(~mask_elegivel).sum()}')

# =============================================================
# ESTRUTURA DO LOG
# =============================================================

log_auditoria = []

def registrar_decisao(contexto, passou_suitability, motivo_bloqueio,
                      acao, tipo_decisao, recompensa):
    """
    Registra uma decisão no log de auditoria.
    Chamada a cada interação, independente do resultado.
    """
    registro = {
        'timestamp':          datetime.now().isoformat(),
        'age':                contexto['Age'],
        'experience':         contexto['Experience'],
        'income':             contexto['Income'],
        'family':             contexto['Family'],
        'education':          contexto['Education'],
        'securities_account': contexto['Securities Account'],
        'cd_account':         contexto['CD Account'],
        'online':             contexto['Online'],
        'credit_card':        contexto['CreditCard'],
        'passou_suitability': passou_suitability,
        'motivo_bloqueio':    motivo_bloqueio,   # None se passou
        'acao':               acao,              # 0 ou 1
        'tipo_decisao':       tipo_decisao,      # 'explotacao', 'exploracao' ou 'bloqueado'
        'recompensa':         recompensa         # 1.0, -0.1, 0.0 ou None se ainda não observada
    }
    log_auditoria.append(registro)


# =============================================================
# FLUXO COMPLETO DE UMA DECISÃO — com log
# =============================================================
def tomar_decisao(cliente, bandit, observar_recompensa=None):
    contexto = pd.DataFrame([cliente])

    # --- PASSO 1: suitability ---
    elegivel, motivo = verificar_suitability(cliente)

    if not elegivel:
        registrar_decisao(
            contexto=cliente,
            passou_suitability=False,
            motivo_bloqueio=motivo,
            acao=0,
            tipo_decisao='bloqueado',
            recompensa=0.0
        )
        return 0

    # --- PASSO 2: bandit decide ---
    acao = bandit.predict()

    # Detecta exploração replicando a lógica do EpsilonGreedy
    tipo_decisao = 'exploracao' if np.random.random() < 0.2 else 'explotacao'

    # --- PASSO 3: observar recompensa ---
    recompensa = None
    if observar_recompensa:
        resultado_real = observar_recompensa(cliente)
        recompensa = calcular_recompensa(acao, resultado_real)

    # --- PASSO 4: registrar ---
    registrar_decisao(
        contexto=cliente,
        passou_suitability=True,
        motivo_bloqueio=None,
        acao=acao,
        tipo_decisao=tipo_decisao,
        recompensa=recompensa
    )

    # --- PASSO 5: bandit aprende ---
    if recompensa is not None:
        bandit.partial_fit(
            decisions=[acao],
            rewards=[recompensa]
        )

    return acao

# =============================================================
# SALVAR O LOG
# =============================================================

def salvar_log(caminho='log_auditoria.csv'):
    """
    Converte o log em DataFrame e salva em CSV.
    Chamada ao final de cada sessão ou periodicamente.
    """
    df_log = pd.DataFrame(log_auditoria)
    df_log.to_csv(caminho, index=False)
    print(f"Log salvo: {len(df_log)} registros em '{caminho}'")
    return df_log