# Plano MLOps — Plataforma de Experimentação Adaptativa

**Projeto**: Datathon 7MLET  
**Versão**: 1.0  
**Data**: Janeiro/2025

---

## 1. Visão Geral do Ciclo de Vida

O ciclo de vida do modelo segue quatro fases contínuas:

```
Experimento → Avaliação → Aprovação → Produção
     ↑                                    |
     └──────────── Monitoramento ─────────┘
```

---

## 2. Versionamento de Política

Cada versão da política é identificada por:

| Campo | Descrição | Exemplo |
|-------|-----------|---------|
| versão | Semântica major.minor | 1.2 |
| algoritmo | Nome do algoritmo | EpsilonGreedy |
| epsilon | Taxa de exploração | 0.2 |
| data_treino | Data do retreino | 2025-01-15 |
| n_interacoes | Interações de treino | 5000 |
| recompensa_media | Métrica de qualidade | 0.1616 |
| golden_set_score | Score no golden set | 25/25 |
| status | Estado atual | production/staging/archived |

**Política atual em produção**: v1.0 — EpsilonGreedy(epsilon=0.2)

---

## 3. Critérios de Retreino

O retreino é disparado automaticamente quando qualquer condição abaixo
é detectada pelo monitoramento contínuo:

| Critério | Threshold | Janela de Observação |
|----------|-----------|---------------------|
| Queda de recompensa média | > 15% abaixo da baseline | 7 dias |
| Drift na distribuição de contexto | KS test p-value < 0.05 | 14 dias |
| Taxa de conversão abaixo do esperado | < 10% entre elegíveis | 7 dias |
| Taxa de bloqueio anormal | > 40% ou < 15% | 3 dias |
| Erro no golden set | < 23/25 (< 92%) | A cada deploy |

---

## 4. Pipeline de Retreino

```
TRIGGER (Azure Monitor alerta ou manual)
        ↓
1. COLETA DE DADOS
   - Carrega log de auditoria dos últimos N dias (Azure SQL)
   - Filtra interações com recompensa observada
   - Valida qualidade dos dados (mínimo 500 interações)
        ↓
2. RETREINO
   - Reinicializa bandit com histórico balanceado
   - Executa partial_fit com dados coletados
   - Registra experimento no MLflow
        ↓
3. AVALIAÇÃO
   - Roda golden set (mínimo 23/25 para prosseguir)
   - Calcula recompensa média nos últimos 30 dias
   - Compara com política atual em produção
        ↓
4. APPROVAL GATE (humano no loop)
   - Notificação automática ao responsável
   - Prazo de aprovação: 48 horas
   - Se não aprovado: rollback automático para versão anterior
        ↓
5. PROMOÇÃO
   - Modelo versionado no Azure ML
   - Imagem Docker atualizada no Azure Container Registry
   - Deploy gradual: 10% → 50% → 100% do tráfego
        ↓
6. MONITORAMENTO PÓS-DEPLOY
   - Comparação A/B por 7 dias
   - Se nova versão inferior: rollback automático
```

---

## 5. Approval Gate

O approval gate é a etapa de aprovação humana obrigatória antes de
qualquer nova política ir para produção.

**Responsáveis**:
- Aprovação técnica: Engenheiro de ML
- Aprovação de negócio: Product Owner
- Aprovação de compliance: Analista de Risco

**Critérios mínimos para aprovação**:
- Golden set score >= 23/25
- Recompensa média >= recompensa da versão atual
- Nenhuma violação de suitability nos testes
- Documentação do model card atualizada

**Procedimento**:
1. Sistema gera relatório automático comparando versão nova vs atual
2. Responsáveis recebem notificação com link para o relatório
3. Aprovação registrada com timestamp e justificativa
4. Qualquer responsável pode vetar — exige revisão antes de prosseguir

---

## 6. Procedimento de Rollback

**Rollback automático** é disparado quando:
- Nova versão tem recompensa média < 90% da versão anterior após 24h
- Golden set score cai abaixo de 23/25 em produção
- Taxa de erro > 1% nas chamadas ao decisor

**Rollback manual** pode ser executado a qualquer momento pelo responsável.

**Procedimento de rollback**:
```bash
# 1. Identifica versão anterior aprovada
python src/mlops/listar_versoes.py --status production

# 2. Carrega versão anterior
python src/mlops/rollback.py --versao 1.0

# 3. Valida golden set
python src/avaliacao_offline.py

# 4. Registra rollback no MLflow
# (automático via script)
```

**SLA de rollback**: máximo 15 minutos após decisão.

---

## 7. Monitoramento de Drift

### 7.1 Drift de contexto
Monitora se a distribuição das variáveis de entrada mudou:
- Teste KS (Kolmogorov-Smirnov) entre distribuição atual e baseline
- Alertas quando p-value < 0.05 para Income, Age ou Family

### 7.2 Drift de recompensa
Monitora se a recompensa média está degradando:
- Média móvel de 7 dias vs baseline dos primeiros 30 dias
- Alerta quando queda > 15%

### 7.3 Drift de suitability
Monitora se as taxas de bloqueio estão anormais:
- Taxa de bloqueio esperada: 15-25% dos clientes
- Alerta se sair dessa faixa por mais de 3 dias consecutivos

---

## 8. Rastreio de Experimentos (MLflow)

Todos os experimentos são rastreados com MLflow:

**Parâmetros registrados**:
- Algoritmo e hiperparâmetros (epsilon, k)
- Tamanho do histórico de inicialização
- Semente aleatória
- Data e versão do dataset

**Métricas registradas**:
- Recompensa total e média
- Regret acumulado
- Taxa de conversão
- Taxa de exploração
- Golden set score

**Artefatos registrados**:
- Modelo serializado (.pkl)
- Log de auditoria resumido
- Gráficos de recompensa e regret
- Resultado do golden set

---

## 9. Revisão Periódica

| Artefato | Cadência | Responsável |
|----------|----------|-------------|
| Model Card | A cada retreino | Engenheiro de ML |
| System Card | Trimestral | Tech Lead |
| Plano LGPD | Semestral | DPO / Compliance |
| Critérios de drift | Semestral | Engenheiro de ML |
| Golden set | A cada mudança de política | Engenheiro de ML |
