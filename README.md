# Plataforma de Experimentação Adaptativa — Datathon 7MLET

Plataforma de decisão adaptativa para ofertas financeiras em canais digitais,
baseada em Multi-Armed Bandit com aprendizado online, filtro de suitability,
log de auditoria e assistente analítico com LLM.

---

## Problema

Uma instituição financeira digital precisa decidir, em tempo real, se deve
exibir um banner de oferta de empréstimo pessoal para cada cliente elegível.
Regras fixas desperdiçam tráfego e não se adaptam a mudanças de comportamento.
Testes A/B longos demoram para reagir. Este projeto propõe uma política
adaptativa baseada em Multi-Armed Bandit que aprende continuamente com as
interações observadas.

---

## Abordagem

O sistema usa um **Contextual Bandit com EpsilonGreedy** (MABWiser) inicializado
com histórico sintético balanceado. A cada interação:

1. O cliente passa por um **filtro de suitability** (regras de elegibilidade)
2. O **bandit decide** se exibe ou não o banner
3. O resultado é **observado** (converteu ou não)
4. O bandit **aprende** com o resultado via `partial_fit`
5. A decisão é **registrada** no log de auditoria

Um **assistente analítico** (LLM via API Anthropic) responde perguntas sobre
decisões, desempenho e políticas internas consultando o log e documentos RAG.

---

## Resultados

| Estratégia | Recompensa total | Média por interação |
|---|---|---|
| Mostrar sempre | +924.1 | +0.1848 |
| **Bandit (EpsilonGreedy)** | **+808.1** | **+0.1616** |
| XGBoost fixo | +632.2 | +0.1264 |
| Aleatório | +451.4 | +0.0903 |
| Não mostrar | +0.0 | +0.0000 |

O bandit supera o XGBoost fixo em +27.6% e o aleatório em +79.0%.
Fica abaixo do "Mostrar sempre" porque esse baseline não tem custo de
penalidade — em ambiente real com comportamento variável, o bandit
leva vantagem por se adaptar continuamente.

---

## Estrutura do projeto

```
datathon-7mlet-lastech/
│
├── src/
│   ├── modelo_xb.py           # XGBoost — inicialização offline
│   ├── modelo_mab.py          # Bandit + suitability + log de auditoria
│   ├── simulador.py           # Simulação + comparação com baselines
│   ├── assistente.py          # Chat analítico com API Anthropic
│   └── painel.py              # Painel de visualizações
│
├── data/
│   ├── kaggle/                # Dataset original (ver instruções abaixo)
│   ├── processed/             # Base tratada sem vazamento
│   ├── synthetic_enrichment/  # Catálogo, eventos e delayed rewards
│   └── golden_set/            # Casos de avaliação offline
│
├── docs/                      # Arquitetura Azure, Model Card, System Card, LGPD
├── notebooks/                 # EDA e análises exploratórias
├── reports/                   # Relatório de geração de dados
├── politicas/                 # Documentos de política interna (RAG)
│
├── README.md
├── pyproject.toml
├── .env.example
├── .gitignore
└── LICENSE
```

---

## Execução local

### 1. Pré-requisitos

- Python 3.10+
- Conta no Kaggle (para baixar o dataset)
- Chave da API Anthropic (para o assistente)

### 2. Instalar dependências

```bash
# Criar ambiente virtual
python -m venv .venv
source .venv/bin/activate  # Linux/Mac
.venv\Scripts\activate     # Windows

# Instalar dependências
pip install -e .
```

### 3. Baixar o dataset

Acesse https://www.kaggle.com/datasets/krantiswalke/bank-personal-loan-modelling,
baixe o arquivo CSV e coloque em `data/kaggle/Bank_Personal_Loan_Modelling.csv`.

### 4. Configurar variáveis de ambiente

```bash
cp .env.example .env
# Edite .env e insira sua chave da API Anthropic
```

### 5. Executar o pipeline completo

```bash
# Passo 1 — Treinar o XGBoost (gera modelo_xgboost.json)
python src/modelo_xb.py

# Passo 2 — Rodar simulação e comparar baselines
python src/simulador.py

# Passo 3 — Gerar painel de visualizações
python src/painel.py

# Passo 4 — Iniciar assistente analítico (requer ANTHROPIC_API_KEY)
python src/assistente.py
```

---

## Componentes principais

### Filtro de Suitability
Bloqueia clientes inelegíveis antes do bandit ser consultado:
- Idade < 21 anos → `idade_abaixo_21`
- Renda < 25 unidades → `renda_abaixo_minimo`
- Sem nenhum produto ativo → `sem_relacionamento_bancario`

### Decisor (Bandit)
- **Algoritmo**: EpsilonGreedy (epsilon=0.2)
- **Biblioteca**: MABWiser
- **Braços**: [0] não mostrar, [1] mostrar banner
- **Inicialização**: histórico sintético balanceado (50/50)
- **Aprendizado**: online via `partial_fit` a cada interação

### Recompensa
- Mostrou + converteu: **+1.0**
- Mostrou + não converteu: **-0.01**
- Não mostrou: **0.0**

### Log de Auditoria
Cada decisão registra: timestamp, contexto do cliente, resultado do
suitability, motivo de bloqueio, ação tomada, tipo de decisão
(exploração/explotação) e recompensa observada.

### Assistente Analítico
Chat em terminal que responde perguntas sobre decisões, desempenho e
políticas internas consultando o log de auditoria, comparação de baselines
e documentos de política via RAG.

---

## Limitações conhecidas

- O bandit não é contextual (sem KNearest) — aprende recompensa média global por braço, não por perfil de cliente
- A detecção de exploração/explotação é aproximada (baseada no epsilon, não no sorteio interno do MABWiser)
- O dataset tem desbalanceamento severo (~9.6% de conversão) que enviesaria a inicialização se usada diretamente
- A verdade oculta do simulador é sintética — não representa comportamento real de clientes

---

## Tecnologias

| Tecnologia | Uso |
|---|---|
| Python 3.10+ | Linguagem principal |
| XGBoost | Modelo base (inicialização offline) |
| MABWiser | Implementação do bandit |
| scikit-learn | Utilitários de ML |
| pandas / numpy | Manipulação de dados |
| matplotlib | Visualizações |
| Anthropic API | LLM para assistente analítico |

---

## Dataset

**Bank Personal Loan Modelling** — Kaggle  
Fonte: https://www.kaggle.com/datasets/krantiswalke/bank-personal-loan-modelling  
Licença: Community Data License Agreement – Sharing – Version 1.0  
5000 clientes, 14 variáveis, target: aceitação de empréstimo pessoal.

---

## Licença

MIT License — veja [LICENSE](LICENSE) para detalhes.
