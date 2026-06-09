"""
Análise Exploratória de Dados — Bank Personal Loan Modelling

Projeto: Plataforma de Experimentação Adaptativa — Datathon 7MLET
Dataset: Bank Personal Loan Modelling (Kaggle)
Objetivo: Entender a base, identificar variáveis relevantes, documentar
decisões de pré-processamento e justificar o uso no contexto de Multi-Armed Bandit.
"""

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.gridspec as gridspec
import os
import warnings
warnings.filterwarnings('ignore')

# Configurações de visualização
plt.rcParams['figure.figsize'] = (12, 5)
plt.rcParams['font.size'] = 11

print("Bibliotecas carregadas com sucesso.")

# ================================================================
# 1. CARREGAMENTO E VISÃO GERAL
# ================================================================

print("\n" + "="*60)
print("1. CARREGAMENTO E VISÃO GERAL")
print("="*60)

df = pd.read_csv('../data/kaggle/Bank_Personal_Loan_Modelling.csv')

print(f"Dimensões: {df.shape[0]} linhas x {df.shape[1]} colunas")
print(f"\nPrimeiras linhas:")
print(df.head())

print("\n=== Tipos de dados e valores não-nulos ===")
df.info()

print("\n=== Estatísticas Descritivas ===")
print(df.describe().round(2))

# ================================================================
# 2. DICIONÁRIO DE DADOS
# ================================================================

print("\n" + "="*60)
print("2. DICIONÁRIO DE DADOS")
print("="*60)

dicionario = {
    'Coluna': ['ID', 'Age', 'Experience', 'Income', 'ZIP Code', 'Family',
               'CCAvg', 'Education', 'Mortgage', 'Personal Loan',
               'Securities Account', 'CD Account', 'Online', 'CreditCard'],
    'Tipo': ['int', 'int', 'int', 'int', 'int', 'int',
             'float', 'int', 'int', 'int', 'int', 'int', 'int', 'int'],
    'Uso no Projeto': ['Descartada', 'Contexto do bandit', 'Contexto (após limpeza)',
                       'Contexto + suitability', 'Descartada', 'Contexto do bandit',
                       'Não utilizada', 'Contexto do bandit', 'Não utilizada',
                       'Target / Recompensa histórica', 'Contexto + suitability',
                       'Contexto + suitability', 'Contexto do bandit', 'Contexto + suitability']
}
print(pd.DataFrame(dicionario).to_string(index=False))

# ================================================================
# 3. QUALIDADE DOS DADOS
# ================================================================

print("\n" + "="*60)
print("3. QUALIDADE DOS DADOS")
print("="*60)

print("\n=== Valores Nulos por Coluna ===")
nulos = df.isnull().sum()
pct_nulos = (nulos / len(df) * 100).round(2)
resumo_nulos = pd.DataFrame({'Nulos': nulos, '% Nulos': pct_nulos})
if resumo_nulos['Nulos'].sum() > 0:
    print(resumo_nulos[resumo_nulos['Nulos'] > 0])
else:
    print("Nenhum valor nulo encontrado.")

duplicados = df.duplicated().sum()
print(f"\nRegistros duplicados: {duplicados}")
print(f"Registros únicos: {len(df) - duplicados}")

print("\n=== Problema: Experience com valores negativos ===")
exp_negativo = df[df['Experience'] < 0]
print(f"Registros com Experience < 0: {len(exp_negativo)}")
print(f"Valores encontrados: {sorted(df['Experience'].unique())[:10]}")
print(f"\nDecisão: remover registros com Experience < 0 (valores inválidos)")
print(f"Registros restantes após limpeza: {len(df[df['Experience'] >= 0])}")

# ================================================================
# 4. ANÁLISE DO TARGET
# ================================================================

print("\n" + "="*60)
print("4. ANÁLISE DO TARGET — Personal Loan")
print("="*60)

contagem = df['Personal Loan'].value_counts()
pct = df['Personal Loan'].value_counts(normalize=True) * 100

fig, axes = plt.subplots(1, 2, figsize=(12, 4))

axes[0].bar(['Não aceitou (0)', 'Aceitou (1)'],
            contagem.values,
            color=['#e74c3c', '#2ecc71'])
axes[0].set_title('Distribuição do Target — Personal Loan')
axes[0].set_ylabel('Quantidade')
for i, v in enumerate(contagem.values):
    axes[0].text(i, v + 30, f'{v}\n({pct.values[i]:.1f}%)',
                ha='center', fontweight='bold')

axes[1].pie(contagem.values,
            labels=[f'Não aceitou\n{pct.values[0]:.1f}%',
                    f'Aceitou\n{pct.values[1]:.1f}%'],
            colors=['#e74c3c', '#2ecc71'],
            startangle=90)
axes[1].set_title('Proporção do Target')

plt.tight_layout()
os.makedirs('../reports', exist_ok=True)
plt.savefig('../reports/target_distribution.png', dpi=150, bbox_inches='tight')
plt.show()

print(f"\nDesbalanceamento: {pct.values[0]:.1f}% não aceitou vs {pct.values[1]:.1f}% aceitou")
print("Impacto: XGBoost treinado com scale_pos_weight para compensar desbalanceamento")

# ================================================================
# 5. ANÁLISE DAS VARIÁVEIS DE CONTEXTO
# ================================================================

print("\n" + "="*60)
print("5. ANÁLISE DAS VARIÁVEIS DE CONTEXTO")
print("="*60)

variaveis = ['Age', 'Experience', 'Income', 'Family', 'Education']

fig, axes = plt.subplots(1, 5, figsize=(18, 4))

for i, var in enumerate(variaveis):
    axes[i].hist(df[var], bins=20, color='#3498db', alpha=0.7, edgecolor='white')
    axes[i].set_title(var)
    axes[i].set_xlabel('Valor')
    if i == 0:
        axes[i].set_ylabel('Frequência')

plt.suptitle('Distribuição das Variáveis Numéricas de Contexto', y=1.02)
plt.tight_layout()
plt.savefig('../reports/numeric_distributions.png', dpi=150, bbox_inches='tight')
plt.show()

binarias = ['Securities Account', 'CD Account', 'Online', 'CreditCard']

fig, axes = plt.subplots(1, 4, figsize=(14, 4))

for i, var in enumerate(binarias):
    contagem_var = df[var].value_counts()
    axes[i].bar(['Não (0)', 'Sim (1)'], contagem_var.values,
                color=['#e74c3c', '#2ecc71'])
    axes[i].set_title(var)
    axes[i].set_ylabel('Quantidade')
    for j, v in enumerate(contagem_var.values):
        axes[i].text(j, v + 20, str(v), ha='center', fontweight='bold')

plt.suptitle('Distribuição das Variáveis Binárias de Contexto', y=1.02)
plt.tight_layout()
plt.savefig('../reports/binary_distributions.png', dpi=150, bbox_inches='tight')
plt.show()

# Correlação com o target
colunas_modelo = ['Age', 'Experience', 'Income', 'Family', 'Education',
                  'Securities Account', 'CD Account', 'Online', 'CreditCard']

correlacoes = df[colunas_modelo + ['Personal Loan']].corr()['Personal Loan'].drop('Personal Loan')
correlacoes = correlacoes.sort_values(ascending=True)

fig, ax = plt.subplots(figsize=(10, 5))
cores = ['#e74c3c' if v < 0 else '#2ecc71' for v in correlacoes.values]
ax.barh(correlacoes.index, correlacoes.values, color=cores)
ax.axvline(x=0, color='black', linewidth=0.8)
ax.set_title('Correlação das Variáveis com Personal Loan (Target)')
ax.set_xlabel('Correlação de Pearson')
ax.grid(True, alpha=0.3, axis='x')

for i, v in enumerate(correlacoes.values):
    ax.text(v + 0.005 if v >= 0 else v - 0.005,
            i, f'{v:.3f}',
            va='center',
            ha='left' if v >= 0 else 'right',
            fontsize=9)

plt.tight_layout()
plt.savefig('../reports/correlations.png', dpi=150, bbox_inches='tight')
plt.show()

print("\nVariáveis com maior correlação com o target:")
print(correlacoes.abs().sort_values(ascending=False).head(5))

# ================================================================
# 6. ANÁLISE DE SUITABILITY
# ================================================================

print("\n" + "="*60)
print("6. ANÁLISE DE SUITABILITY")
print("="*60)

df_clean = df[df['Experience'] >= 0].copy()

bloq_idade = (df_clean['Age'] < 21).sum()
bloq_renda = (df_clean['Income'] < 25).sum()
bloq_relacionamento = (
    (df_clean['CreditCard'] == 0) &
    (df_clean['CD Account'] == 0) &
    (df_clean['Securities Account'] == 0)
).sum()

mask_bloqueado = (
    (df_clean['Age'] < 21) |
    (df_clean['Income'] < 25) |
    ((df_clean['CreditCard'] == 0) &
     (df_clean['CD Account'] == 0) &
     (df_clean['Securities Account'] == 0))
)

total_bloqueado = mask_bloqueado.sum()
total_elegivel = (~mask_bloqueado).sum()

print("=== Impacto do Filtro de Suitability na Base ===\n")
print(f"Total de registros (após limpeza): {len(df_clean)}")
print(f"\nBloqueados por idade < 21:              {bloq_idade}")
print(f"Bloqueados por renda < 25:              {bloq_renda}")
print(f"Bloqueados por sem relacionamento:      {bloq_relacionamento}")
print(f"\nTotal bloqueado (pelo menos 1 regra):   {total_bloqueado} ({total_bloqueado/len(df_clean)*100:.1f}%)")
print(f"Total elegível:                         {total_elegivel} ({total_elegivel/len(df_clean)*100:.1f}%)")

taxa_elegivel = df_clean[~mask_bloqueado]['Personal Loan'].mean() * 100
taxa_bloqueado = df_clean[mask_bloqueado]['Personal Loan'].mean() * 100
print(f"\nTaxa de conversão entre elegíveis:      {taxa_elegivel:.1f}%")
print(f"Taxa de conversão entre bloqueados:     {taxa_bloqueado:.1f}%")
print("\nConclusão: O filtro remove clientes com menor propensão, concentrando")
print("o sistema nos perfis com maior potencial de conversão.")

# ================================================================
# 7. SALVAR BASE PROCESSADA
# ================================================================

print("\n" + "="*60)
print("7. SALVAR BASE PROCESSADA")
print("="*60)

df_processed = df[df['Experience'] >= 0][
    ['Age', 'Experience', 'Income', 'Family', 'Education',
     'Securities Account', 'CD Account', 'Online', 'CreditCard', 'Personal Loan']
].copy()

os.makedirs('../data/processed', exist_ok=True)
df_processed.to_csv('../data/processed/bank_loan_processed.csv', index=False)

print(f"Base processada salva em data/processed/bank_loan_processed.csv")
print(f"Dimensões: {df_processed.shape[0]} linhas x {df_processed.shape[1]} colunas")
print(f"\nPrimeiras linhas:")
print(df_processed.head())

print("\n" + "="*60)
print("EDA CONCLUÍDA COM SUCESSO")
print("Arquivos gerados:")
print("  - reports/target_distribution.png")
print("  - reports/numeric_distributions.png")
print("  - reports/binary_distributions.png")
print("  - reports/correlations.png")
print("  - data/processed/bank_loan_processed.csv")
print("="*60)
