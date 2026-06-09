# Model Card — Bandit de Decisão Adaptativa

**Nome do modelo**: EpsilonGreedy Contextual Bandit  
**Versão**: 1.0  
**Data**: Janeiro/2025  
**Projeto**: Plataforma de Experimentação Adaptativa — Datathon 7MLET  
**Responsável**: Felipe Gonçalves

---

## 1. Descrição do Modelo

Sistema de decisão adaptativa que determina, em tempo real, se um banner
de oferta de empréstimo pessoal deve ser exibido para um cliente elegível
de uma instituição financeira digital.

O modelo usa o algoritmo EpsilonGreedy (MABWiser) com aprendizado online
via `partial_fit`, inicializado com histórico sintético balanceado.

---

## 2. Uso Pretendido

### 2.1 Uso adequado
- Decidir se exibir oferta de empréstimo pessoal em canais digitais
- Personalizar comunicação de produto financeiro para clientes elegíveis
- Experimentos adaptativos em ambiente controlado e auditável

### 2.2 Usos fora do escopo
- Decisões de concessão de crédito (aprovação/reprovação de empréstimos)
- Precificação de produtos financeiros
- Avaliação de risco individual de inadimplência
- Qualquer decisão com impacto regulatório direto sem humano no loop
- Uso em populações fora do perfil de treinamento (ex: clientes corporativos)

---

## 3. Dados de Treinamento

| Campo | Valor |
|-------|-------|
| Dataset | Bank Personal Loan Modelling (Kaggle) |
| Fonte | https://www.kaggle.com/datasets/krantiswalke/bank-personal-loan-modelling |
| Registros | 4.948 (após limpeza) |
| Variáveis de entrada | 9 variáveis demográficas e financeiras |
| Target original | Personal Loan (aceitação de empréstimo) |
| Período | Dados históricos sem data definida |
| Limitação | Dados sintéticos americanos — não representam clientes brasileiros |

---

## 4. Dados de Avaliação

| Campo | Valor |
|-------|-------|
| Golden set | 25 casos documentados |
| Score golden set | 25/25 (100%) |
| Simulação | 5.000 interações sintéticas |
| Ambiente de simulação | Verdade oculta com 3 segmentos de propensão |

---

## 5. Métricas de Performance

| Métrica | Valor | Contexto |
|---------|-------|---------|
| Recompensa total (5k interações) | +808.1 | vs +924.1 do mostrar sempre |
| Recompensa média por interação | +0.1616 | vs +0.1848 do mostrar sempre |
| Superioridade vs XGBoost fixo | +27.8% | Modelo estático sem adaptação |
| Superioridade vs aleatório | +79.1% | Decisão aleatória |
| Regret total (5k interações) | 98.0 | ~0.02 por interação |
| Regret médio por interação | 0.0196 | Inclui exploração intencional |
| Taxa de conversão (elegíveis) | ~18% | Ambiente simulado |
| Taxa de exploração | ~20% | Controlado pelo epsilon=0.2 |
| Golden set score | 25/25 | 100% de acerto |
| Violações de suitability | 0 | Nenhuma em todos os testes |

---

## 6. Análise de Fairness

### 6.1 Grupos protegidos
O sistema não utiliza variáveis de gênero, raça, religião ou outras
características protegidas por lei. As variáveis utilizadas são:
Age, Experience, Income, Family, Education e produtos financeiros.

### 6.2 Análise de exposição por segmento

| Segmento | Critério | Taxa de Elegibilidade | Decisão |
|----------|----------|----------------------|---------|
| Jovens (< 21 anos) | Age < 21 → bloqueado | 0% | Proteção regulatória |
| Baixa renda | Income < 25 → bloqueado | 0% | Proteção financeira |
| Sem relacionamento | Sem produtos → bloqueado | 0% | Insuficiência de dados |
| Alta propensão | Income > 150, Family >= 4 | 100% dos elegíveis | Priorizado |
| Média propensão | Income > 100, CD Account | 100% dos elegíveis | Elegível |
| Baixa propensão | Demais elegíveis | 100% dos elegíveis | Elegível |

### 6.3 Limitações de fairness
- O critério de renda mínima (Income < 25) pode impactar desproporcionalmente
  populações de menor poder aquisitivo
- O critério de relacionamento bancário pode excluir clientes recém-chegados
  ao sistema financeiro formal
- A verdade oculta do simulador assume correlação entre renda/família e
  propensão — essa hipótese deve ser validada com dados reais

---

## 7. Vieses Conhecidos

| Viés | Descrição | Mitigação |
|------|-----------|-----------|
| Viés de inicialização | Histórico balanceado 50/50 pode não refletir distribuição real | Monitorar e retreinar com dados reais |
| Viés de desbalanceamento | Dataset com ~9.6% de conversão | Tratado com scale_pos_weight no XGBoost |
| Viés de simulação | Verdade oculta com apenas 3 segmentos | Simplificação consciente — documentada |
| Viés de seleção | Clientes bloqueados nunca recebem oferta | Intencional por regra de negócio |
| Viés de exploração | 20% das decisões são aleatórias | Necessário para aprendizado contínuo |

---

## 8. Limitações Técnicas

- O bandit não é contextual nesta versão — aprende recompensa média global
  por braço, não por perfil de cliente
- Delayed rewards não são incorporados ao aprendizado online
- O sistema não modela sazonalidade ou variações temporais
- A detecção de exploração/explotação é aproximada (baseada no epsilon)
- Sem mecanismo de esquecimento — interações antigas têm peso permanente

---

## 9. Revisão e Manutenção

| Evento | Ação |
|--------|------|
| Retreino | Atualizar métricas neste model card |
| Mudança de algoritmo | Criar nova versão do model card |
| Revisão semestral | Verificar vieses e limitações |
| Incidente de suitability | Revisão imediata obrigatória |

**Próxima revisão programada**: Julho/2025
