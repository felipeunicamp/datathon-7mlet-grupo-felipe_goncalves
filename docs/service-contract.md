# Contrato de Serviço — Plataforma de Experimentação Adaptativa

**Versão**: 1.0  
**Data**: Janeiro/2025

---

## 1. Visão Geral

O sistema recebe o perfil de um cliente e devolve uma decisão:
exibir (1) ou não exibir (0) o banner de oferta de empréstimo pessoal,
junto com metadados de auditoria.

---

## 2. Entrada

### 2.1 Formato
Dicionário Python com 9 variáveis obrigatórias.

### 2.2 Schema

| Campo | Tipo | Restrições | Descrição |
|-------|------|-----------|-----------|
| Age | int | >= 0 | Idade do cliente em anos |
| Experience | int | >= 0 | Anos de experiência profissional |
| Income | int | >= 0 | Renda mensal em unidades de referência |
| Family | int | 1-4 | Tamanho do núcleo familiar |
| Education | int | 1-3 | Nível de escolaridade |
| Securities Account | int | 0 ou 1 | Possui conta de investimentos |
| CD Account | int | 0 ou 1 | Possui certificado de depósito |
| Online | int | 0 ou 1 | Usa internet banking |
| CreditCard | int | 0 ou 1 | Possui cartão de crédito |

### 2.3 Exemplo de entrada válida
```python
cliente = {
    "Age": 35,
    "Experience": 10,
    "Income": 80,
    "Family": 2,
    "Education": 2,
    "Securities Account": 1,
    "CD Account": 0,
    "Online": 1,
    "CreditCard": 1
}
```

---

## 3. Saída

### 3.1 Retorno direto
A função `tomar_decisao()` retorna um inteiro:
- `1` — exibir o banner
- `0` — não exibir o banner

### 3.2 Log de auditoria
Cada chamada registra automaticamente no `log_auditoria`:

| Campo | Tipo | Descrição |
|-------|------|-----------|
| timestamp | str (ISO) | Momento da decisão |
| age | int | Idade do cliente |
| experience | int | Experiência do cliente |
| income | int | Renda do cliente |
| family | int | Família do cliente |
| education | int | Escolaridade do cliente |
| securities_account | int | Conta de investimentos |
| cd_account | int | Certificado de depósito |
| online | int | Uso de internet banking |
| credit_card | int | Cartão de crédito |
| passou_suitability | bool | Se passou no filtro |
| motivo_bloqueio | str ou None | Razão do bloqueio |
| acao | int | Decisão tomada (0 ou 1) |
| tipo_decisao | str | blocked / exploracao / explotacao |
| recompensa | float ou None | Recompensa observada |

### 3.3 Reason codes

| Código | Significado |
|--------|------------|
| `bloqueado` | Cliente não passou no filtro de suitability |
| `exploracao` | Decisão aleatória (20% do tempo — epsilon) |
| `explotacao` | Decisão baseada no aprendizado acumulado |

### 3.4 Motivos de bloqueio

| Código | Regra |
|--------|-------|
| `idade_abaixo_21` | Age < 21 |
| `renda_abaixo_minimo` | Income < 25 |
| `sem_relacionamento_bancario` | CreditCard=0 E CD Account=0 E Securities Account=0 |

---

## 4. Tratamento de Erros

| Situação | Comportamento |
|----------|--------------|
| Variável ausente no contexto | KeyError — validar entrada antes |
| Variável com tipo inválido | Comportamento indefinido — validar entrada |
| Bandit não inicializado | AttributeError — executar modelo_mab.py primeiro |
| Dataset não encontrado | FileNotFoundError — verificar data/kaggle/ |

---

## 5. Exemplo de Chamada Completa

```python
from modelo_mab import bandit, tomar_decisao, salvar_log

cliente = {
    "Age": 35,
    "Experience": 10,
    "Income": 80,
    "Family": 2,
    "Education": 2,
    "Securities Account": 1,
    "CD Account": 0,
    "Online": 1,
    "CreditCard": 1
}

# Tomar decisão (com recompensa simulada)
def minha_recompensa(c):
    return 1  # substituir pela recompensa real

acao = tomar_decisao(cliente, bandit, observar_recompensa=minha_recompensa)
print(f"Decisão: {'Mostrar banner' if acao == 1 else 'Não mostrar'}")

# Salvar log
salvar_log('log_auditoria.csv')
```

---

## 6. Pipeline Ponta a Ponta

Comando único para reproduzir o pipeline completo:

```bash
cd /caminho/do/projeto

# 1. Treinar modelo base
python src/modelo_xb.py

# 2. Rodar simulação e comparação
python src/simulador.py

# 3. Gerar visualizações
python src/painel.py

# 4. Rodar avaliação offline
python src/avaliacao_offline.py

# 5. Rodar testes automatizados
python -m pytest src/tests/test_sistema.py -v

# 6. Iniciar assistente analítico
python src/assistente.py
```

---

## 7. Versão da Política

| Campo | Valor |
|-------|-------|
| Algoritmo | EpsilonGreedy |
| Epsilon | 0.2 |
| Braços | [0, 1] |
| Inicialização | Histórico balanceado 50/50 |
| Versão | 1.0 |
| Data | Janeiro/2025 |
