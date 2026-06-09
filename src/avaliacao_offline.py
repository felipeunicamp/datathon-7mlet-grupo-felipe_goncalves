"""
Avaliação Offline — Golden Set
==============================
Avalia o sistema contra os 25 casos do golden set.
Verifica se o filtro de suitability e o bandit tomam
as decisões esperadas para cada caso documentado.

Execução:
    cd /home/felipedeoliveiragoncalves/PycharmProjects/lastech
    python src/avaliacao_offline.py
"""

import json
import pandas as pd
import numpy as np
import sys
import os

# Adiciona src ao path para importar módulos locais
sys.path.insert(0, os.path.join(os.path.dirname(__file__)))

from modelo_mab import bandit, verificar_suitability, calcular_recompensa

# ================================================================
# CARREGAR GOLDEN SET
# ================================================================

def carregar_golden_set(caminho='data/golden_set/evaluation_cases.jsonl'):
    casos = []
    with open(caminho, 'r', encoding='utf-8') as f:
        for linha in f:
            linha = linha.strip()
            if linha:
                casos.append(json.loads(linha))
    return casos


# ================================================================
# AVALIAR UM CASO
# ================================================================

def avaliar_caso(caso):
    """
    Avalia um caso do golden set contra o sistema.
    Retorna dict com resultado do teste.
    """
    contexto = caso['context']
    esperado_suitability = caso['expected_suitability']
    esperado_acao = caso['expected_action']
    pass_criteria = caso['pass_criteria']

    # Testa suitability
    elegivel, motivo_bloqueio = verificar_suitability(contexto)

    # Testa ação do bandit (se elegível)
    if elegivel:
        acao = bandit.predict()
    else:
        acao = 0

    # Avalia pass/fail
    suitability_correto = (elegivel == esperado_suitability)

    # Para casos bloqueados, verifica motivo
    motivo_correto = True
    if not esperado_suitability and 'block_reason' in pass_criteria:
        motivo_esperado = pass_criteria.split('block_reason=')[1].split(' ')[0]
        motivo_correto = (motivo_bloqueio == motivo_esperado)

    # Para casos elegíveis com ação esperada fixa
    acao_correta = True
    if esperado_suitability and 'action=1' in pass_criteria and 'action IN' not in pass_criteria:
        acao_correta = (acao == 1)
    elif not esperado_suitability:
        acao_correta = (acao == 0)

    passou = suitability_correto and motivo_correto and acao_correta

    return {
        'case_id': caso['case_id'],
        'category': caso['category'],
        'passou': passou,
        'suitability_correto': suitability_correto,
        'acao_correta': acao_correta,
        'motivo_correto': motivo_correto,
        'elegivel_obtido': elegivel,
        'elegivel_esperado': esperado_suitability,
        'acao_obtida': acao,
        'acao_esperada': esperado_acao,
        'motivo_bloqueio': motivo_bloqueio,
        'justificativa': caso['justification']
    }


# ================================================================
# RODAR AVALIAÇÃO COMPLETA
# ================================================================

def rodar_avaliacao():
    print("=" * 65)
    print("AVALIAÇÃO OFFLINE — GOLDEN SET")
    print("=" * 65)

    casos = carregar_golden_set()
    print(f"\nTotal de casos carregados: {len(casos)}\n")

    resultados = []
    for caso in casos:
        resultado = avaliar_caso(caso)
        resultados.append(resultado)

        status = "✓ PASS" if resultado['passou'] else "✗ FAIL"
        print(f"  Caso {caso['case_id']:>2} [{caso['category']:<15}] {status}")
        if not resultado['passou']:
            print(f"         Suitability: esperado={resultado['elegivel_esperado']} obtido={resultado['elegivel_obtido']}")
            print(f"         Ação: esperada={resultado['acao_esperada']} obtida={resultado['acao_obtida']}")
            print(f"         Motivo bloqueio: {resultado['motivo_bloqueio']}")

    # ================================================================
    # MÉTRICAS GERAIS
    # ================================================================

    df = pd.DataFrame(resultados)
    total = len(df)
    passou = df['passou'].sum()
    falhou = total - passou

    print("\n" + "=" * 65)
    print("RESUMO")
    print("=" * 65)
    print(f"\n  Total de casos    : {total}")
    print(f"  Passou (PASS)     : {passou} ({passou/total*100:.1f}%)")
    print(f"  Falhou (FAIL)     : {falhou} ({falhou/total*100:.1f}%)")

    print("\n--- Por categoria ---")
    for categoria in df['category'].unique():
        sub = df[df['category'] == categoria]
        p = sub['passou'].sum()
        t = len(sub)
        print(f"  {categoria:<20}: {p}/{t} passou")

    # ================================================================
    # ANÁLISE DE FAIRNESS
    # ================================================================

    print("\n--- Análise de Fairness ---")
    casos_data = carregar_golden_set()

    elegíveis = [c for c in casos_data if c['expected_suitability']]
    bloqueados = [c for c in casos_data if not c['expected_suitability']]

    print(f"  Casos elegíveis   : {len(elegíveis)}")
    print(f"  Casos bloqueados  : {len(bloqueados)}")

    # Verifica se nenhum bloqueado recebeu banner
    bloqueados_com_banner = df[
        (df['elegivel_esperado'] == False) & (df['acao_obtida'] == 1)
    ]
    print(f"\n  Violações de suitability (bloqueado recebeu banner): {len(bloqueados_com_banner)}")
    if len(bloqueados_com_banner) > 0:
        print("  ⚠️  ATENÇÃO: Violação de suitability detectada!")
        print(bloqueados_com_banner[['case_id', 'category', 'motivo_bloqueio']])
    else:
        print("  ✓ Nenhuma violação de suitability detectada")

    # ================================================================
    # SALVAR RESULTADOS
    # ================================================================

    df.to_csv('data/golden_set/evaluation_results.csv', index=False)
    print(f"\nResultados salvos em data/golden_set/evaluation_results.csv")

    print("\n" + "=" * 65)
    if falhou == 0:
        print("✓ TODOS OS CASOS PASSARAM")
    else:
        print(f"⚠️  {falhou} CASO(S) FALHARAM — revisar critérios")
    print("=" * 65)

    return df


# ================================================================
# EXECUÇÃO
# ================================================================

if __name__ == '__main__':
    rodar_avaliacao()
