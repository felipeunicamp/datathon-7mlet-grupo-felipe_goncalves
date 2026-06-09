# Plano LGPD — Plataforma de Experimentação Adaptativa

**Sistema**: Plataforma de Decisão Adaptativa para Ofertas Financeiras  
**Versão**: 1.0  
**Data**: Janeiro/2025  
**DPO Responsável**: A definir

---

## 1. Aviso Legal

Este documento descreve o tratamento de dados em ambiente de
**demonstração acadêmica** com dados sintéticos. Não representa
tratamento de dados pessoais reais. Em produção real, este plano
deve ser revisado por equipe jurídica especializada em LGPD.

---

## 2. Base Legal

| Operação | Base Legal (LGPD Art. 7°) | Justificativa |
|----------|--------------------------|---------------|
| Coleta de dados de perfil | Legítimo interesse (IX) | Personalização de oferta compatível com perfil |
| Decisão automatizada | Legítimo interesse (IX) | Melhoria da experiência do cliente |
| Log de auditoria | Obrigação legal (II) | Rastreabilidade exigida por regulação financeira |
| Retreino do modelo | Legítimo interesse (IX) | Melhoria contínua da política de oferta |

---

## 3. Finalidade do Tratamento

| Dado | Finalidade | Compatível com coleta? |
|------|-----------|----------------------|
| Perfil demográfico (Age, Family) | Decisão de exibição de oferta | Sim |
| Perfil financeiro (Income) | Filtro de suitability | Sim |
| Produtos ativos (CreditCard, etc) | Filtro de suitability | Sim |
| Log de decisão | Auditoria e retreino | Sim |
| Timestamp da interação | Rastreabilidade temporal | Sim |

---

## 4. Minimização de Dados

O sistema coleta apenas o mínimo necessário para a decisão:

**Dados utilizados** (9 variáveis):
Age, Experience, Income, Family, Education,
Securities Account, CD Account, Online, CreditCard

**Dados explicitamente NÃO coletados**:
- Nome, CPF ou qualquer identificador direto
- Endereço ou geolocalização
- Dados de saúde
- Origem racial ou étnica
- Convicções religiosas ou políticas
- Dados biométricos
- Histórico de transações detalhado
- Saldo de conta corrente

---

## 5. Mapeamento de Identificadores

| Campo no Sistema | Tipo | Identificador Direto? | Tratamento |
|-----------------|------|----------------------|------------|
| Age | Demográfico | Não | Usado diretamente |
| Income | Financeiro | Não | Usado diretamente |
| Family | Demográfico | Não | Usado diretamente |
| timestamp | Temporal | Não (sem vínculo a ID) | Usado para auditoria |
| event_id | Técnico | Não (sequencial) | Interno ao sistema |

**Nota**: o sistema não armazena identificadores diretos (CPF, nome,
número de conta). O log de auditoria registra perfis anônimos.

---

## 6. Ciclo de Retenção de Dados

| Dado | Retenção | Justificativa | Descarte |
|------|----------|---------------|---------|
| Log de auditoria | 5 anos | Obrigação regulatória financeira | Exclusão segura |
| Modelo treinado | Enquanto em produção + 1 ano | Reprodutibilidade | Exclusão do storage |
| Dados de treinamento | 2 anos | Retreino e auditoria | Anonimização + exclusão |
| Experimentos MLflow | 2 anos | Rastreabilidade de versões | Exclusão do banco |
| Delayed rewards | 1 ano | Análise de horizonte temporal | Exclusão |

---

## 7. Atributos Protegidos

Os seguintes atributos são monitorados para evitar discriminação:

| Atributo | Status no Sistema | Monitoramento |
|----------|------------------|---------------|
| Gênero | Não coletado | N/A |
| Raça/Etnia | Não coletado | N/A |
| Religião | Não coletado | N/A |
| Idade | Usado no suitability (≥ 21) | Auditado no golden set |
| Renda | Usado no suitability (≥ 25) | Auditado no golden set |

**Análise de fairness**: documentada no Model Card. O critério de
renda mínima pode impactar desproporcionalmente populações de baixa
renda — mitigação via revisão periódica dos critérios.

---

## 8. Política de Logs e Telemetria

| Tipo de Log | Conteúdo | Acesso | Retenção |
|-------------|---------|--------|---------|
| Log de decisão | Perfil anônimo + ação + recompensa | Equipe técnica | 5 anos |
| Log de sistema | Erros, latência, métricas | Equipe técnica | 90 dias |
| Log de auditoria MLflow | Parâmetros e métricas de experimentos | Equipe ML | 2 anos |
| Log do assistente | Perguntas e respostas (sem PII) | Equipe técnica | 30 dias |

**PII nos logs**: nenhum dado pessoal identificável é registrado nos logs.
Perfis são compostos apenas por variáveis agregadas sem identificadores.

---

## 9. Direitos dos Titulares

Em produção real com dados pessoais reais, os seguintes direitos
devem ser garantidos (LGPD Art. 18):

| Direito | Como Exercer | SLA |
|---------|-------------|-----|
| Confirmação de tratamento | Canal de atendimento | 15 dias |
| Acesso aos dados | Canal de atendimento | 15 dias |
| Correção | Canal de atendimento | 15 dias |
| Anonimização/exclusão | Canal de atendimento | 15 dias |
| Portabilidade | Canal de atendimento | 15 dias |
| Oposição ao tratamento | Canal de atendimento | Imediato |
| Revisão de decisão automatizada | Canal de atendimento | 15 dias |

---

## 10. Plano de Resposta a Incidentes

### 10.1 Classificação de incidentes
| Severidade | Descrição | Exemplo |
|-----------|-----------|---------|
| Crítica | Vazamento de dados pessoais | Log com CPF exposto |
| Alta | Violação de suitability | Menor recebeu oferta |
| Média | Acesso não autorizado ao log | Funcionário sem permissão |
| Baixa | Anomalia nos dados | Distribuição inesperada |

### 10.2 Procedimento geral
```
1. Detecção (automática ou manual)
        ↓
2. Classificação de severidade
        ↓
3. Contenção (isolamento do sistema se necessário)
        ↓
4. Notificação interna (DPO + Tech Lead + Compliance)
        ↓
5. [Se crítica/alta] Notificação à ANPD em até 72h
        ↓
6. [Se crítica] Notificação aos titulares afetados
        ↓
7. Investigação e remediação
        ↓
8. Relatório pós-incidente
        ↓
9. Revisão dos controles
```

### 10.3 Contatos de emergência
- DPO: a definir em produção real
- ANPD: https://www.gov.br/anpd/pt-br
- Prazo de notificação à ANPD: 72 horas após conhecimento

---

## 11. Revisão do Plano

Este plano é revisado semestralmente ou após qualquer incidente de
privacidade. Alterações requerem aprovação do DPO e do Compliance.

**Próxima revisão programada**: Julho/2025
