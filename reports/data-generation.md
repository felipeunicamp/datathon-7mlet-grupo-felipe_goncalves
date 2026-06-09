# Relatório de Geração de Dados Sintéticos

**Projeto**: Plataforma de Experimentação Adaptativa — Datathon 7MLET
**Data de geração**: Janeiro/2025
**Semente aleatória**: 42

---

## 1. Objetivo

Criar uma camada sintética de experimentação adaptativa sobre o dataset
Bank Personal Loan Modelling (Kaggle), representando como o sistema de
Multi-Armed Bandit operaria em produção.

---

## 2. Arquivos Gerados

### 2.1 offer_catalog.csv
**Descrição**: Catálogo de braços/ofertas disponíveis para o sistema de decisão.

**Schema**:
| Campo | Tipo | Descrição |
|-------|------|-----------|
| offer_id | int | Identificador único da oferta |
| offer_name | str | Nome descritivo da oferta |
| offer_type | str | Tipo: control ou banner |
| message | str | Texto da mensagem exibida |
| channel | str | Canal de exibição |
| arm_id | int | Braço do bandit (0=não mostrar, 1=mostrar) |
| active | bool | Se a oferta está ativa |
| created_at | date | Data de criação |

**Hipóteses**:
- O sistema opera com 2 braços efetivos: mostrar (1) ou não mostrar (0)
- Variações de mensagem (standard, urgency, benefit) são documentadas
  para experimentos futuros mas mapeadas ao mesmo braço

### 2.2 offer_events.csv
**Descrição**: Registro de 5000 interações simuladas de clientes com o sistema.

**Schema**:
| Campo | Tipo | Descrição |
|-------|------|-----------|
| event_id | int | Identificador único do evento |
| timestamp | datetime | Momento da interação |
| client_* | int | Variáveis de contexto do cliente (9 variáveis) |
| passed_suitability | bool | Se o cliente passou pelo filtro |
| suitability_block_reason | str | Motivo do bloqueio (se aplicável) |
| arm_shown | int | Braço selecionado (0 ou 1) |
| offer_shown | str | Oferta exibida |
| decision_type | str | blocked / exploration / exploitation |
| converted | int | Se o cliente converteu (0/1) |
| immediate_reward | float | Recompensa imediata observada |
| delayed_reward_available | bool | Se há recompensa atrasada associada |

**Hipóteses**:
- Clientes são amostrados com reposição da base processada
- A verdade oculta replica as regras do simulador principal
- EpsilonGreedy com epsilon=0.2: 20% exploração, 80% explotação
- Timestamp simulado: 250 dias de operação (20 eventos/dia)

**Sementes**: np.random.seed(42) global; cada evento usa random_state=i

### 2.3 delayed_rewards.csv
**Descrição**: Recompensas atrasadas para eventos com exibição de banner.

**Schema**:
| Campo | Tipo | Descrição |
|-------|------|-----------|
| event_id | int | Referência ao evento em offer_events.csv |
| original_timestamp | datetime | Momento da interação original |
| reward_timestamp | datetime | Momento da recompensa atrasada |
| delay_days | int | Dias de atraso (1-7) |
| immediate_reward | float | Recompensa imediata original |
| delayed_converted | int | Se houve conversão tardia (0/1) |
| delayed_reward | float | Recompensa adicional do delay |
| total_reward | float | Soma das recompensas |
| reward_type | str | Tipo da recompensa atrasada |

**Hipóteses**:
- 15% dos eventos com banner têm recompensa atrasada
- Delay de 1 a 7 dias (uniforme)
- 8% de probabilidade de conversão tardia para quem não converteu imediatamente
- Clientes que já converteram não geram recompensa adicional

---

## 3. Modelagem do Horizonte Temporal

O sistema opera em dois horizontes:

**Imediato (t=0)**: recompensa observada na mesma sessão
- Conversão imediata: +1.0
- Exibição sem conversão: -0.01
- Sem exibição: 0.0

**Atrasado (t=1 a 7 dias)**: recompensa observada após a interação
- Conversão tardia: +1.0 adicional
- Sem conversão tardia: 0.0 adicional

O bandit principal opera com recompensas imediatas. O arquivo
`delayed_rewards.csv` documenta o horizonte atrasado para análise
offline e retreino futuro.

---

## 4. Tratamento de Cold-Start

O sistema resolve o problema de cold-start de duas formas:

1. **Inicialização offline**: o bandit é inicializado com histórico
   sintético balanceado (50% mostrar / 50% não mostrar) gerado a partir
   dos perfis reais da base processada com a lógica da verdade oculta

2. **Exploração controlada**: epsilon=0.2 garante que 20% das decisões
   sejam exploratórias, permitindo aprendizado contínuo mesmo após
   a convergência inicial

---

## 5. Limitações e Riscos

- **Dados sintéticos**: os eventos não representam comportamento real
  de clientes bancários
- **Verdade oculta simplificada**: apenas 3 segmentos de propensão
  (alta, média, baixa) — a realidade é mais complexa
- **Sem sazonalidade**: os eventos não modelam variações temporais
  (dia da semana, mês, feriados)
- **Reposição com reposição**: clientes podem aparecer múltiplas vezes
  nos eventos, o que não ocorreria em produção real
- **Delayed rewards simplificados**: o horizonte de 7 dias é arbitrário;
  em produção, o horizonte dependeria do produto financeiro
