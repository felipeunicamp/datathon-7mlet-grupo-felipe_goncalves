# Análise Algorítmica — Plataforma de Experimentação Adaptativa

**Projeto**: Datathon 7MLET  
**Versão**: 1.0  
**Data**: Janeiro/2025

---

## 1. Formulação do Problema

O sistema decide, para cada cliente elegível, se deve exibir (braço 1)
ou não exibir (braço 0) um banner de oferta de empréstimo pessoal.

**Estrutura do problema**:
- **Braços**: {0 = não mostrar, 1 = mostrar banner}
- **Contexto**: vetor de 9 variáveis do perfil do cliente
- **Recompensa**: +1.0 (conversão), -0.01 (exibição sem retorno), 0.0 (não exibição)
- **Objetivo**: maximizar recompensa acumulada ao longo das interações

---

## 2. Algoritmos Considerados

### 2.1 Thompson Sampling

**Descrição**: abordagem bayesiana que mantém uma distribuição de probabilidade
sobre a recompensa esperada de cada braço. A cada decisão, sorteia uma amostra
de cada distribuição e escolhe o braço com maior valor amostrado.

**Vantagem**: exploração naturalmente calibrada pela incerteza — braços com
menos dados têm distribuições mais largas e são explorados mais.

**Por que não foi usado**: o MABWiser exige recompensas estritamente binárias
(0 ou 1) para Thompson Sampling. O projeto usa recompensa com penalidade (-0.01),
que é incompatível com essa restrição. Seria necessário remover a penalidade,
o que enfraqueceria o argumento de negócio de evitar exibições desnecessárias.

**Referência**: Thompson, W.R. (1933). On the likelihood that one unknown
probability exceeds another in view of the evidence of two samples.
Biometrika, 25(3/4), 285-294.

---

### 2.2 Nilos-UCB

**Descrição**: variação da família UCB (Upper Confidence Bound) que seleciona
o braço com maior valor combinado de estimativa de recompensa e bônus de
incerteza. A fórmula geral é:

```
UCB(a) = Q(a) + c × sqrt(ln(t) / N(a))
```

Onde:
- Q(a) = estimativa de recompensa do braço a
- N(a) = número de vezes que o braço a foi selecionado
- t = número total de interações
- c = parâmetro de exploração

O Nilos-UCB é uma adaptação que normaliza o bônus de incerteza pelo
desvio padrão das recompensas observadas, tornando-o mais robusto a
variações na escala da recompensa.

**Vantagem sobre EpsilonGreedy**: a exploração é direcionada — braços
com alta incerteza recebem bônus maior, concentrando a exploração onde
ela é mais informativa. No EpsilonGreedy, a exploração é uniforme e aleatória.

**Por que não foi implementado**: o MABWiser não implementa Nilos-UCB
nativamente. Implementar do zero exigiria adaptações para o formato de
recompensa contínua com penalidade usado no projeto. O EpsilonGreedy foi
escolhido como alternativa por ser compatível com recompensas contínuas
e ter comportamento estável com a inicialização balanceada adotada.

**Trabalho futuro**: implementar Nilos-UCB como variação comparativa,
especialmente para avaliar se a exploração direcionada supera o EpsilonGreedy
em cenários com muitos braços ou contexto de alta dimensionalidade.

**Referência**: Auer, P., Cesa-Bianchi, N., & Fischer, P. (2002).
Finite-time analysis of the multiarmed bandit problem.
Machine Learning, 47(2-3), 235-256.

---

### 2.3 EpsilonGreedy — Algoritmo Escolhido

**Descrição**: com probabilidade ε (epsilon), escolhe um braço aleatoriamente
(exploração); com probabilidade 1-ε, escolhe o braço com maior recompensa
média estimada (explotação).

**Configuração adotada**:
- epsilon = 0.2 (20% exploração, 80% explotação)
- Sem política de vizinhança (aprendizado global por braço)
- Recompensas contínuas: +1.0, -0.01, 0.0

**Justificativa da escolha**:
1. Compatível com recompensas contínuas (incluindo penalidade -0.01)
2. Comportamento estável com histórico balanceado de inicialização
3. Controle direto e interpretável da taxa de exploração via epsilon
4. Implementação nativa no MABWiser sem adaptações
5. Suficiente para demonstrar aprendizado adaptativo no escopo do projeto

**Trade-off**: a exploração aleatória do EpsilonGreedy é menos eficiente
que o UCB em cenários com muitos braços, pois não direciona a exploração
para onde a incerteza é maior. Para 2 braços, essa diferença é pequena.

---

## 3. Tratamento de Cold-Start

O problema de cold-start ocorre quando o sistema não tem histórico
suficiente para tomar decisões informadas no início da operação.

**Abordagem adotada — inicialização balanceada**:

O bandit é inicializado com um histórico sintético de 1624 interações
(todos os clientes elegíveis da base), dividido igualmente entre os dois braços:
- 812 decisões "mostrar" (braço 1)
- 812 decisões "não mostrar" (braço 0)

As recompensas são geradas com a mesma lógica da verdade oculta do simulador,
garantindo consistência entre inicialização e aprendizado online.

**Por que não usar as previsões do XGBoost diretamente**:
O XGBoost treinado no dataset retorna probabilidades sistematicamente baixas
(~9.6% de conversão) devido ao desbalanceamento severo da base. Usar essas
probabilidades para gerar o histórico inicial enviesaria o bandit para
"não mostrar" desde o início, prejudicando o aprendizado online.

**Alternativas consideradas**:
- **Warm start com XGBoost**: descartado pelo viés de desbalanceamento
- **Início do zero**: descartado pelo alto regret inicial
- **Inicialização uniforme**: adotada por ser neutra e reproduzível

---

## 4. Tratamento de Delayed Rewards

Recompensas atrasadas ocorrem quando o resultado de uma decisão só é
observado dias após a interação (ex: cliente clicou no banner mas
contratou o empréstimo uma semana depois).

**Modelagem adotada**:

O sistema opera em dois horizontes temporais:

**Horizonte imediato (t=0)**:
- Recompensa observada na mesma sessão
- Usada diretamente no `partial_fit` do bandit
- Valores: +1.0 (conversão), -0.01 (sem conversão), 0.0 (não exibido)

**Horizonte atrasado (t=1 a 7 dias)**:
- 15% dos eventos com banner têm recompensa atrasada
- 8% de probabilidade de conversão tardia
- Documentado em `data/synthetic_enrichment/delayed_rewards.csv`
- **Não incorporado ao aprendizado online** nesta versão

**Limitação**: o bandit atual aprende apenas com recompensas imediatas.
Incorporar delayed rewards exigiria uma fila de recompensas pendentes
e atualização retroativa do modelo — implementação prevista como
trabalho futuro no ciclo MLOps.

---

## 5. Métricas de Avaliação

| Métrica | Descrição | Resultado |
|---------|-----------|-----------|
| Recompensa total | Soma das recompensas acumuladas | +808.1 (bandit) |
| Recompensa média | Média por interação | +0.1616 |
| Regret acumulado | Perda vs política ótima | Ver gráfico |
| Taxa de exploração | % decisões exploratórias | ~20% (epsilon=0.2) |
| Taxa de conversão | % interações com conversão | ~18% entre elegíveis |
| Taxa de bloqueio | % clientes bloqueados pelo suitability | ~19.8% |

---

## 6. Comparação Quantitativa

| Estratégia | Recompensa Total | vs Bandit |
|------------|-----------------|-----------|
| Mostrar sempre | +924.1 | -13.7% |
| **Bandit (EpsilonGreedy)** | **+808.1** | **—** |
| XGBoost fixo | +632.2 | +27.8% |
| Aleatório | +451.4 | +79.1% |
| Não mostrar | +0.0 | — |

O bandit supera o XGBoost fixo em **+27.8%** e o aleatório em **+79.1%**.
Fica abaixo do "Mostrar sempre" porque esse baseline não tem custo de
penalidade e captura 100% das conversões — comportamento ótimo apenas
em ambientes estáticos com penalidade baixa.

Em ambiente dinâmico (comportamento dos clientes muda ao longo do tempo),
o bandit leva vantagem por se adaptar continuamente sem necessidade de retreino.
