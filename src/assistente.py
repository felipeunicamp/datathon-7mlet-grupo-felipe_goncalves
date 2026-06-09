"""
Chat analítico que responde perguntas sobre o sistema.
Usa a API da Anthropic + documentos locais como contexto.
"""

import pandas as pd
import os
import anthropic

# =============================================================
# PARTE 1 — CARREGAR AS FONTES DE DADOS
# =============================================================

def carregar_log():
    if not os.path.exists('log_auditoria.csv'):
        return "Log de auditoria ainda não gerado."
    df = pd.read_csv('log_auditoria.csv')
    resumo = f"""
    Total de decisões registradas : {len(df)}
    Clientes bloqueados            : {(df['passou_suitability'] == False).sum()}
    Banner mostrado                : {(df['acao'] == 1).sum()}
    Decisões de exploração         : {(df['tipo_decisao'] == 'exploracao').sum()}
    Recompensa média               : {df['recompensa'].mean():.4f}
    Motivos de bloqueio            : {df[df['passou_suitability'] == False]['motivo_bloqueio'].value_counts().to_dict()}
    """
    return resumo

def carregar_baselines():
    if not os.path.exists('comparacao_baselines.csv'):
        return "Comparação de baselines ainda não gerada."
    df = pd.read_csv('comparacao_baselines.csv')
    resumo = {}
    for coluna in df.columns:
        resumo[coluna] = f"Recompensa total: {df[coluna].iloc[-1]:+.1f}"
    return str(resumo)

def carregar_politicas():
    textos = []
    pasta = 'politicas'
    if not os.path.exists(pasta):
        return "Pasta de políticas não encontrada."
    for arquivo in os.listdir(pasta):
        if arquivo.endswith('.txt'):
            with open(f'{pasta}/{arquivo}', 'r', encoding='utf-8') as f:
                textos.append(f"=== {arquivo} ===\n{f.read()}")
    return "\n\n".join(textos)


# =============================================================
# PARTE 2 — MONTAR O CONTEXTO PARA O MODELO
# =============================================================

def montar_contexto():
    """
    Junta todas as fontes em um único texto de contexto.
    Esse texto é enviado para o modelo junto com a pergunta.
    """
    return f"""
Você é um assistente analítico de uma instituição financeira digital.
Responda perguntas sobre decisões do sistema, desempenho de experimentos
e políticas internas com base nas informações abaixo.
Seja direto e objetivo. Se a informação não estiver disponível, diga isso.

### LOG DE AUDITORIA (resumo)
{carregar_log()}

### COMPARAÇÃO DE BASELINES
{carregar_baselines()}

### POLÍTICAS INTERNAS
{carregar_politicas()}
"""

# =============================================================
# PARTE 3 — O CHAT
# =============================================================

def chat():
    cliente_api = anthropic.Anthropic()
    contexto    = montar_contexto()
    historico   = []

    print("\n" + "=" * 55)
    print("ASSISTENTE ANALÍTICO — Plataforma de Experimentação")
    print("Digite 'sair' para encerrar")
    print("=" * 55 + "\n")

    while True:
        pergunta = input("Você: ").strip()

        if pergunta.lower() == 'sair':
            print("Encerrando assistente.")
            break

        if not pergunta:
            continue

        # Adiciona a pergunta ao histórico
        historico.append({
            "role": "user",
            "content": pergunta
        })

        # Chama a API com contexto + histórico completo
        resposta = cliente_api.messages.create(
            model="claude-sonnet-4-20250514",
            max_tokens=1000,
            system=contexto,
            messages=historico
        )

        texto_resposta = resposta.content[0].text

        # Adiciona a resposta ao histórico para manter contexto
        historico.append({
            "role": "assistant",
            "content": texto_resposta
        })

        print(f"\nAssistente: {texto_resposta}\n")


# =============================================================
# EXECUÇÃO
# =============================================================

if __name__ == '__main__':
    chat()