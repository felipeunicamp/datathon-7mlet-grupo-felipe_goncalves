# System Card — Plataforma de Experimentação Adaptativa

**Sistema**: Plataforma de Decisão Adaptativa para Ofertas Financeiras  
**Versão**: 1.0  
**Data**: Janeiro/2025  
**Projeto**: Datathon 7MLET

---

## 1. Escopo do Sistema

O sistema decide, em tempo real, se um banner de oferta de empréstimo
pessoal deve ser exibido para cada cliente elegível em canais digitais
de uma instituição financeira digital.

**O sistema NÃO**:
- Aprova ou reprova pedidos de crédito
- Define taxas ou condições do empréstimo
- Acessa dados bancários reais
- Toma decisões com consequências jurídicas diretas

---

## 2. Fluxo de Decisão

```
Cliente acessa canal digital
        ↓
Filtro de Suitability
(regras determinísticas obrigatórias)
        ↓
[Bloqueado] → Log com motivo → Fim
        ↓
[Elegível] → Bandit Contextual
        ↓
Decisão: Mostrar (1) ou Não Mostrar (0)
        ↓
Log de Auditoria (sempre)
        ↓
[Se mostrou] → Observa recompensa
        ↓
Aprendizado online (partial_fit)
```

---

## 3. Dependências do Sistema

| Componente | Versão | Criticidade |
|------------|--------|-------------|
| Python | 3.10+ | Alta |
| MABWiser | 2.7+ | Alta — núcleo do decisor |
| XGBoost | 2.0+ | Média — inicialização offline |
| pandas / numpy | latest | Alta — manipulação de dados |
| Anthropic API | latest | Média — assistente analítico |
| MLflow | latest | Baixa — rastreio de experimentos |

---

## 4. Guardrails

### 4.1 Guardrails obrigatórios (não contornáveis)
- Filtro de suitability executa ANTES do bandit — sem exceções
- Clientes com Age < 21 nunca recebem oferta
- Clientes com Income < 25 nunca recebem oferta
- Clientes sem nenhum produto ativo nunca recebem oferta
- Toda decisão é registrada em log imutável

### 4.2 Guardrails de exploração
- Taxa de exploração máxima: 20% (epsilon=0.2)
- Exploração ocorre apenas dentro dos clientes elegíveis
- Nenhuma exploração para clientes bloqueados

### 4.3 Guardrails de qualidade
- Golden set validado a cada retreino (mínimo 23/25)
- Approval gate humano obrigatório antes de produção
- Rollback automático se performance degrada > 15%

---

## 5. Cenários de Risco

### 5.1 Reward Hacking
**Descrição**: o bandit aprende a maximizar recompensa de formas não
intencionadas (ex: mostrar para todos indiscriminadamente).

**Mitigação**:
- Penalidade de -0.01 para exibições sem conversão
- Monitoramento da taxa de exibição (alerta se > 95% dos elegíveis)
- Revisão periódica da função de recompensa

### 5.2 Manipulação do Contexto
**Descrição**: dados de entrada corrompidos ou manipulados para forçar
uma decisão específica.

**Mitigação**:
- Validação de schema na entrada (contrato de dados documentado)
- Variáveis binárias validadas como 0 ou 1
- Log auditável permite detecção post-hoc

### 5.3 Abuso do Assistente Analítico
**Descrição**: usuário tenta extrair informações sensíveis ou
manipular o assistente para contornar políticas.

**Mitigação**:
- Assistente responde apenas com base no contexto fornecido
- Não tem acesso a dados individuais identificáveis
- Respostas são baseadas em agregados do log

### 5.4 Violação de Suitability
**Descrição**: bug ou configuração incorreta permite que cliente
bloqueado receba oferta.

**Mitigação**:
- Filtro de suitability é camada independente do bandit
- Testes automatizados verificam todas as regras (25/25)
- Golden set inclui casos adversariais específicos para suitability
- Alerta imediato se violação detectada em produção

### 5.5 Degradação Silenciosa
**Descrição**: performance do bandit degrada gradualmente sem alerta.

**Mitigação**:
- Monitoramento de recompensa média com janela de 7 dias
- Alertas automáticos no Azure Monitor
- Retreino periódico com critérios documentados

---

## 6. Plano de Monitoramento

| Métrica | Frequência | Alerta | Ação |
|---------|-----------|--------|------|
| Recompensa média | Diário | < 85% da baseline | Investigar + possível retreino |
| Taxa de bloqueio | Diário | < 15% ou > 40% | Revisar regras de suitability |
| Taxa de conversão | Semanal | < 10% entre elegíveis | Revisar verdade oculta |
| Golden set score | A cada deploy | < 23/25 | Bloquear deploy + revisar |
| Drift de contexto | Semanal | KS p-value < 0.05 | Retreino com novos dados |
| Erros de sistema | Tempo real | > 1% de erros | Rollback imediato |

---

## 7. Humano no Loop

As seguintes decisões requerem aprovação humana obrigatória:

| Decisão | Responsável | SLA |
|---------|-------------|-----|
| Promoção de nova versão para produção | Engenheiro ML + PO | 48h |
| Alteração nas regras de suitability | Compliance + Tech Lead | 72h |
| Mudança na função de recompensa | Engenheiro ML + PO | 48h |
| Rollback de versão | Engenheiro ML | 15 min |
| Resposta a incidente de suitability | Todos os responsáveis | Imediato |

---

## 8. Revisão e Manutenção

**Revisão semestral** obrigatória cobrindo:
- Cenários de risco (novos cenários identificados?)
- Guardrails (ainda adequados?)
- Dependências (atualizações necessárias?)
- Incidentes ocorridos no período

**Próxima revisão programada**: Julho/2025
