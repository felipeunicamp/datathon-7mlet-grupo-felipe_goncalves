# Dataset — Bank Personal Loan Modelling

## Fonte
- **Nome**: Bank Personal Loan Modelling
- **Plataforma**: Kaggle
- **Link**: https://www.kaggle.com/datasets/krantiswalke/bank-personal-loan-modelling
- **Versão**: 1.0
- **Licença**: Community Data License Agreement – Sharing – Version 1.0

## Como baixar
1. Acesse o link acima no Kaggle
2. Faça download do arquivo `Bank_Personal_Loan_Modelling.csv`
3. Coloque o arquivo em `data/kaggle/`

## Descrição
Base com 5000 clientes de um banco, contendo perfil demográfico,
financeiro e comportamental. O target é `Personal Loan` — se o cliente
aceitou ou não uma oferta de empréstimo pessoal em campanha anterior.

## Colunas utilizadas
| Coluna | Tipo | Descrição |
|--------|------|-----------|
| Age | int | Idade do cliente |
| Experience | int | Anos de experiência profissional |
| Income | int | Renda mensal (em unidades) |
| Family | int | Tamanho do núcleo familiar |
| Education | int | Nível de escolaridade (1=graduação, 2=pós, 3=avançado) |
| Securities Account | int | Possui conta de investimentos (0/1) |
| CD Account | int | Possui certificado de depósito (0/1) |
| Online | int | Usa internet banking (0/1) |
| CreditCard | int | Possui cartão de crédito (0/1) |
| Personal Loan | int | **Target** — aceitou empréstimo (0/1) |

## Colunas descartadas e justificativa
| Coluna | Motivo do descarte |
|--------|-------------------|
| ID | Identificador sem valor preditivo |
| ZIP Code | Dado geográfico sensível sem valor preditivo |
| Experience negativo | Valores inválidos (-1, -2, -3) removidos |
| Mortgage | Não utilizado neste experimento |
| CCAvg | Não utilizado neste experimento |

## Limitações
- Base desbalanceada: ~9.6% de conversão (Personal Loan = 1)
- Dados sintéticos americanos — não representam comportamento brasileiro
- Ausência de variável temporal — não permite análise de séries temporais
- Renda em unidades abstratas — não mapeadas para moeda real
