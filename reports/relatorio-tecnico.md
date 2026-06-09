# Relatório Técnico — Plataforma de Experimentação Adaptativa

**Projeto**: Datathon 7MLET  
**Autor**: Felipe Gonçalves  
**Data**: Janeiro/2025  
**Versão**: 1.0

---

## 1. Problema

Instituições financeiras digitais enfrentam o desafio de decidir, em
tempo real, qual oferta ou mensagem apresentar para cada cliente elegível
nos canais digitais. Abordagens tradicionais apresentam limitações sérias:

**Regras fixas** não se adaptam a mudanças de comportamento dos clientes
e exigem revisão manual frequente. **Testes A/B longos** desperdiçam
tráfego no braço perdedor por semanas ou meses antes de uma conclusão.
**Modelos preditivos estáticos** são treinados em batch e ficam desatualizados
rapidamente quando o comportamento muda.

O desafio central não é prever quem vai converter — é construir um sistema
que teste hipóteses, valide contexto e aprenda com respostas observadas
sem congelar a decisão em regras estáticas.

**Problema específico**: decidir, para cada cliente elegível que acessa
o canal digital, se o banner de oferta de empréstimo pessoal deve ser
exibido, maximizando conversões e minimizando exposições desnecessárias.

---

## 2. Base de Dados Escolhida

**Dataset**: Bank Personal Loan Modelling (Kaggle)  
**Fonte**: https://www.kaggle.com/datasets/krantiswalke/bank-personal-loan-modelling  
**Licença**: Community Data License Agreement – Sharing – Version 1.0

### 2.1 Justificativa da escolha
O dataset contém 5.000 registros de clientes de um banco com perfil
demográfico, financeiro e comportamental, e um target binário indicando
se o cliente aceitou uma oferta de empréstimo pessoal em campanha anterior.
É compatível com o cenário do desafio e não contém variáveis de vazamento
temporal como `duration` (presente no Bank Marketing UCI).

### 2.2 Pré-processamento
- **Registros removidos**: 52 com `Experience < 0` (valores inválidos)
- **Colunas descartadas**: ID, ZIP Code, CCAvg, Mortgage
- **Variáveis utilizadas**: 9 variáveis demográficas e financeiras
- **Desbalanceamento**: 90.4% não converteu vs 9.6% converteu
- **Tratamento**: `scale_pos_weight` no XGBoost para compensar

### 2.3 Análise exploratória — principais achados
- `Income` tem maior correlação com o target (0.502)
- `CD Account` é o segundo mais correlacionado (0.316)
- Nenhum valor nulo encontrado
- 67.2% dos clientes são bloqueados pelo filtro de suitability

---

## 3. Enriquecimento Sintético

Sobre o dataset original, foi criada uma camada sintética de
experimentação com três artefatos:

**offer_catalog.csv**: catálogo de 4 ofertas disponíveis (1 controle +
3 variações de banner) mapeadas para 2 braços efetivos do bandit.

**offer_events.csv**: 5.000 eventos simulados de interação, com contexto
do cliente, decisão do sistema, tipo de decisão (exploração/explotação/
bloqueado) e recompensa imediata observada.

**delayed_rewards.csv**: recompensas atrasadas para 15% dos eventos com
banner, simulando conversões tardias com horizonte de 1-7 dias.

A geração usa semente aleatória controlada (seed=42) para reprodutibilidade.

---

## 4. Modelagem como Multi-Armed Bandit

### 4.1 Formulação
O problema foi formulado como um bandit de 2 braços:
- **Braço 0**: não exibir o banner
- **Braço 1**: exibir o banner de empréstimo pessoal

O **contexto** é o vetor de 9 variáveis do perfil do cliente.
A **recompensa** é: +1.0 (conversão), -0.01 (exibição sem retorno), 0.0 (não exibição).

### 4.2 Algoritmo escolhido: EpsilonGreedy
O algoritmo EpsilonGreedy (MABWiser, epsilon=0.2) foi escolhido por:
- Compatibilidade com recompensas contínuas (incluindo penalidade -0.01)
- Comportamento estável com inicialização balanceada
- Controle direto e interpretável da taxa de exploração
- Implementação nativa no MABWiser sem adaptações

**Thompson Sampling** foi descartado pela restrição a recompensas binárias
no MABWiser. **Nilos-UCB** foi considerado mas não implementado nativamente —
seria implementado como trabalho futuro para comparação de exploração dirigida.

### 4.3 Tratamento de Cold-Start
O bandit é inicializado com histórico sintético balanceado (812 decisões
de cada braço), gerado com a lógica da verdade oculta do simulador. Isso
evita o viés que ocorreria usando as previsões do XGBoost diretamente
(desbalanceamento severo de ~9.6% de conversão no dataset).

### 4.4 Tratamento de Delayed Rewards
O sistema opera com recompensas imediatas no aprendizado online. Delayed
rewards são documentados em arquivo separado para análise offline e
incorporação em ciclos futuros de retreino.

### 4.5 Modelo base (XGBoost)
Um classificador XGBoost foi treinado no dataset histórico com
`scale_pos_weight` para compensar o desbalanceamento. Acurácia de ~95%
no conjunto de teste. O XGBoost serve como baseline de comparação —
não como inicializador direto do bandit.

---

## 5. Comparação Quantitativa

A comparação foi realizada com 5.000 interações sintéticas, mesma semente
aleatória para todas as estratégias (seed=100), garantindo comparabilidade.

| Estratégia | Recompensa Total | Recompensa Média | vs Bandit |
|------------|-----------------|-----------------|-----------|
| Mostrar sempre | +924.1 | +0.1848 | -13.7% |
| **Bandit (EpsilonGreedy)** | **+808.1** | **+0.1616** | **—** |
| XGBoost fixo | +632.2 | +0.1264 | +27.8% |
| Aleatório | +451.4 | +0.0903 | +79.1% |
| Não mostrar | +0.0 | +0.0000 | — |

**Regret**: 98.0 acumulado em 5.000 interações (0.0196 por interação).

O bandit supera o XGBoost fixo em **+27.8%** — demonstrando que o
aprendizado online agrega valor sobre o modelo estático. Fica abaixo do
"Mostrar sempre" porque esse baseline não tem custo de penalidade e captura
100% das conversões em ambiente estático. Em ambiente dinâmico com
mudança de comportamento, o bandit leva vantagem por se adaptar
continuamente sem retreino.

---

## 6. Avaliação Offline e Golden Set

O golden set contém 25 casos documentados cobrindo:
- 5 casos típicos (clientes elegíveis normais)
- 5 casos de borda (limites exatos das regras de suitability)
- 5 casos bloqueados (violações das regras)
- 5 casos adversariais (tentativas de contornar o sistema)
- 5 casos por segmento de propensão (alta, média, baixa)

**Resultado**: 25/25 (100%) de acerto.  
**Violações de suitability**: 0 em todos os casos.

---

## 7. Arquitetura-Alvo Azure

A solução é operada integralmente em Azure, cobrindo:

**Compute**: Azure Container Apps hospeda o decisor com auto-scaling.
Azure Functions processa delayed rewards e dispara retreino.

**API**: Azure API Management como gateway com autenticação AAD e
rate limiting.

**Dados**: Azure Blob Storage (modelos e logs), Azure SQL Database
(log de auditoria estruturado), Azure ML Datasets (versionamento).

**IA/RAG**: Azure OpenAI (GPT-4o) para o assistente analítico.
Azure AI Search para recuperação semântica das políticas internas.

**Segurança**: Azure Key Vault centraliza segredos. Managed Identity
elimina credenciais no código. AAD para autenticação e RBAC.

**Observabilidade**: Application Insights para métricas de decisão.
Azure Monitor para alertas e dashboards de drift.

**Estimativa de custo**: ~$200-310/mês em ambiente de demonstração.

---

## 8. Ciclo MLOps

O ciclo de vida segue quatro fases: Experimento → Avaliação →
Aprovação → Produção, com monitoramento contínuo.

**Rastreio**: MLflow registra parâmetros, métricas e artefatos de
cada experimento. Backend SQLite local; Azure ML em produção.

**Critérios de retreino**: queda de recompensa > 15%, drift de
contexto (KS test p < 0.05), ou taxa de conversão < 10%.

**Approval gate**: aprovação humana obrigatória (Engenheiro ML +
Product Owner + Compliance) antes de qualquer promoção para produção.

**Rollback**: automático se performance degrada > 15% após deploy.
Manual disponível a qualquer momento com SLA de 15 minutos.

---

## 9. Limitações

**Técnicas**:
- Bandit não é contextual — aprende recompensa global por braço
- Delayed rewards não incorporados ao aprendizado online
- Sem modelagem de sazonalidade ou tendências temporais
- Detecção de exploração/explotação é aproximada

**De dados**:
- Dataset sintético americano — não representa clientes brasileiros
- Verdade oculta simplificada com apenas 3 segmentos de propensão
- Desbalanceamento severo (~9.6% de conversão) limita sinal positivo
- Clientes amostrados com reposição — não representam fluxo real

**De negócio**:
- Penalidade de -0.01 pequena demais para superar "Mostrar sempre"
  em ambiente estático
- Critério de renda mínima pode excluir populações vulneráveis
- Sem modelagem de fadiga de comunicação (múltiplas exposições)

---

## 10. Riscos e Hipóteses

**Hipótese central**: existe sinal preditivo suficiente nas variáveis
demográficas e financeiras para que o bandit aprenda a distinguir perfis
de alta e baixa propensão. **Validada** pela correlação de Income (0.502)
e pelo desempenho superior ao aleatório (+79.1%).

**Hipótese de negócio**: reduzir exposições desnecessárias melhora
a experiência do cliente e reduz custos de comunicação. **Plausível**
mas não testada com dados reais.

**Risco principal**: reward hacking — bandit aprende a mostrar para
todos indiscriminadamente. Mitigado pela penalidade de -0.01 e
monitoramento da taxa de exibição.

**Risco regulatório**: uso de Age e Income em decisões automatizadas
pode ter implicações regulatórias em ambiente real. Mitigado pelo
filtro de suitability determinístico e pelo humano no loop.

---

## 11. Trabalhos Futuros

- Implementar Nilos-UCB para comparação com EpsilonGreedy
- Tornar o bandit contextual com KNearest ou LinUCB
- Incorporar delayed rewards ao aprendizado online
- Modelar sazonalidade e tendências temporais
- Validar com dados reais de clientes brasileiros
- Implementar mecanismo de esquecimento para drift gradual
- Expandir para múltiplos braços (variações de mensagem e canal)

---

## 12. Referências

1. Thompson, W.R. (1933). On the likelihood that one unknown probability
   exceeds another. Biometrika, 25(3/4), 285-294.

2. Auer, P., Cesa-Bianchi, N., & Fischer, P. (2002). Finite-time analysis
   of the multiarmed bandit problem. Machine Learning, 47(2-3), 235-256.

3. Lattimore, T., & Szepesvári, C. (2020). Bandit Algorithms.
   Cambridge University Press.

4. MABWiser: A Parallelizable Contextual Multi-Armed Bandit Library.
   https://github.com/fmr-llc/mabwiser

5. XGBoost: A Scalable Tree Boosting System. Chen & Guestrin (2016).
   KDD 2016.

6. Bank Personal Loan Modelling — Kaggle.
   https://www.kaggle.com/datasets/krantiswalke/bank-personal-loan-modelling

7. Lei Geral de Proteção de Dados — Lei nº 13.709/2018.
   https://www.planalto.gov.br/ccivil_03/_ato2015-2018/2018/lei/l13709.htm

8. MLflow: A Machine Learning Lifecycle Platform.
   https://mlflow.org
