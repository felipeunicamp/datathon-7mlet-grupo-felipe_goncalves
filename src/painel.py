"""
Painel de resultados da plataforma de experimentação adaptativa.
Lê os arquivos gerados pelos passos anteriores e gera visualizações.
"""

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.gridspec as gridspec

# =============================================================
# PARTE 1 — CARREGAR DADOS
# =============================================================

def carregar_dados():
    try:
        log = pd.read_csv('log_auditoria.csv')
    except FileNotFoundError:
        print("ERRO: log_auditoria.csv não encontrado.")
        print("Execute o 03_simulador.py primeiro.")
        return None, None

    try:
        baselines = pd.read_csv('comparacao_baselines.csv')
    except FileNotFoundError:
        print("ERRO: comparacao_baselines.csv não encontrado.")
        print("Execute o 03_simulador.py primeiro.")
        return None, None

    return log, baselines

# =============================================================
# PARTE 2 — GRÁFICO 1: CURVA DE APRENDIZADO
# =============================================================

def grafico_curva_aprendizado(ax, baselines):
    """
    Recompensa acumulada ao longo do tempo para cada estratégia.
    O bandit deve crescer mais rápido que os outros.
    """
    cores = {
        'Mostrar sempre': '#e74c3c',
        'Não mostrar':    '#95a5a6',
        'Aleatório':      '#f39c12',
        'XGBoost fixo':   '#3498db',
        'Bandit':         '#2ecc71',
    }

    for coluna in baselines.columns:
        cor   = cores.get(coluna, '#333333')
        estilo = '-' if coluna == 'Bandit' else '--'
        largura = 2.5 if coluna == 'Bandit' else 1.2
        ax.plot(baselines[coluna],
                label=coluna,
                color=cor,
                linestyle=estilo,
                linewidth=largura)

    ax.set_title('Curva de Aprendizado — Recompensa Acumulada',
                 fontsize=13, fontweight='bold', pad=12)
    ax.set_xlabel('Número de interações')
    ax.set_ylabel('Recompensa acumulada')
    ax.legend(loc='upper left', fontsize=9)
    ax.grid(True, alpha=0.3)
    ax.axhline(y=0, color='black', linewidth=0.5)


# =============================================================
# PARTE 3 — GRÁFICO 2: DISTRIBUIÇÃO DE DECISÕES
# =============================================================

def grafico_distribuicao_decisoes(ax, log):
    """
    Pizza com o destino de cada cliente:
    bloqueado / banner mostrado / banner não mostrado
    """
    bloqueados    = (log['passou_suitability'] == False).sum()
    mostrou       = ((log['passou_suitability'] == True) & (log['acao'] == 1)).sum()
    nao_mostrou   = ((log['passou_suitability'] == True) & (log['acao'] == 0)).sum()

    valores = [bloqueados, mostrou, nao_mostrou]
    labels  = [
        f'Bloqueados\n({bloqueados})',
        f'Banner exibido\n({mostrou})',
        f'Banner não exibido\n({nao_mostrou})'
    ]
    cores   = ['#e74c3c', '#2ecc71', '#3498db']
    explode = [0.05, 0.05, 0.05]

    ax.pie(valores,
           labels=labels,
           colors=cores,
           explode=explode,
           autopct='%1.1f%%',
           startangle=90,
           textprops={'fontsize': 9})

    ax.set_title('Distribuição de Decisões',
                 fontsize=13, fontweight='bold', pad=12)


# =============================================================
# PARTE 4 — GRÁFICO 3: EXPLORAÇÃO VS EXPLOTAÇÃO
# =============================================================

def grafico_exploracao(ax, log):
    """
    Mostra ao longo do tempo a proporção de decisões
    de exploração vs explotação em janelas de 100.
    """
    elegíveis = log[log['passou_suitability'] == True].copy()
    elegíveis = elegíveis.reset_index(drop=True)

    tamanho_janela = 100
    blocos  = []
    taxas   = []

    for inicio in range(0, len(elegíveis), tamanho_janela):
        bloco = elegíveis.iloc[inicio:inicio + tamanho_janela]
        taxa  = (bloco['tipo_decisao'] == 'exploracao').mean()
        blocos.append(inicio + tamanho_janela)
        taxas.append(taxa)

    ax.fill_between(blocos, taxas, alpha=0.3, color='#9b59b6')
    ax.plot(blocos, taxas, color='#9b59b6', linewidth=2)
    ax.axhline(y=0.2, color='red', linestyle='--',
               linewidth=1, label='Referência de exploração')

    ax.set_title('Taxa de Exploração ao Longo do Tempo',
                 fontsize=13, fontweight='bold', pad=12)
    ax.set_xlabel('Número de interações')
    ax.set_ylabel('Proporção de exploração')
    ax.set_ylim(0, 1)
    ax.legend(fontsize=9)
    ax.grid(True, alpha=0.3)


# =============================================================
# PARTE 5 — GRÁFICO 4: RECOMPENSA MÉDIA POR BLOCO
# =============================================================

def grafico_recompensa_por_bloco(ax, log):
    """
    Recompensa média em janelas de 100 interações.
    Deve crescer ao longo do tempo se o bandit aprendeu.
    """
    elegíveis = log[log['passou_suitability'] == True].copy()
    elegíveis = elegíveis.reset_index(drop=True)

    tamanho_janela = 100
    blocos  = []
    medias  = []

    for inicio in range(0, len(elegíveis), tamanho_janela):
        bloco = elegíveis.iloc[inicio:inicio + tamanho_janela]
        media = bloco['recompensa'].mean()
        blocos.append(inicio + tamanho_janela)
        medias.append(media)

    cores = ['#e74c3c' if m < 0 else '#2ecc71' for m in medias]

    ax.bar(blocos, medias, width=80, color=cores, alpha=0.8)
    ax.axhline(y=0, color='black', linewidth=0.8)

    # Linha de tendência
    if len(blocos) > 1:
        z = np.polyfit(blocos, medias, 1)
        p = np.poly1d(z)
        ax.plot(blocos, p(blocos), '--',
                color='#2c3e50', linewidth=1.5,
                label='Tendência')
        ax.legend(fontsize=9)

    ax.set_title('Recompensa Média por Bloco de 100 Interações',
                 fontsize=13, fontweight='bold', pad=12)
    ax.set_xlabel('Número de interações')
    ax.set_ylabel('Recompensa média')
    ax.grid(True, alpha=0.3, axis='y')


# =============================================================
# PARTE 6 — MONTAR E SALVAR O PAINEL
# =============================================================

def gerar_painel():
    log, baselines = carregar_dados()
    if log is None:
        return

    fig = plt.figure(figsize=(16, 12))
    fig.suptitle(
        'Plataforma de Experimentação Adaptativa — Painel de Resultados',
        fontsize=15, fontweight='bold', y=0.98
    )

    gs = gridspec.GridSpec(2, 2, figure=fig,
                           hspace=0.4, wspace=0.3)

    ax1 = fig.add_subplot(gs[0, :])   # curva ocupa linha inteira
    ax2 = fig.add_subplot(gs[1, 0])
    ax3 = fig.add_subplot(gs[1, 1])

    grafico_curva_aprendizado(ax1, baselines)
    grafico_distribuicao_decisoes(ax2, log)
    grafico_exploracao(ax3, log)

    plt.savefig('painel_resultados.png',
                dpi=150, bbox_inches='tight',
                facecolor='white')
    print("Painel salvo em 'painel_resultados.png'")

    # Painel secundário — recompensa por bloco separada
    fig2, ax4 = plt.subplots(figsize=(12, 5))
    grafico_recompensa_por_bloco(ax4, log)
    plt.tight_layout()
    plt.savefig('recompensa_por_bloco.png',
                dpi=150, bbox_inches='tight',
                facecolor='white')
    print("Gráfico de evolução salvo em 'recompensa_por_bloco.png'")

    plt.show()


# =============================================================
# EXECUÇÃO
# =============================================================

if __name__ == '__main__':
    gerar_painel()