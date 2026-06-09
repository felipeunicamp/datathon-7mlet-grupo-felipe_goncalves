"""
Testes Automatizados — Plataforma de Experimentação Adaptativa
==============================================================
Suíte mínima de testes cobrindo:
- Contratos de dados (entrada e saída)
- Filtro de suitability
- Decisão do bandit
- Registro de auditoria
- Recompensa

Execução:
    cd /home/felipedeoliveiragoncalves/PycharmProjects/lastech
    python -m pytest src/tests/test_sistema.py -v
"""

import sys
import os
import pytest
import pandas as pd
import numpy as np

# Adiciona src ao path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from modelo_mab import (
    verificar_suitability,
    calcular_recompensa,
    tomar_decisao,
    log_auditoria,
    bandit
)


# ================================================================
# FIXTURES — perfis de clientes para reuso nos testes
# ================================================================

@pytest.fixture
def cliente_elegivel():
    return {
        'Age': 35, 'Experience': 10, 'Income': 80,
        'Family': 2, 'Education': 2,
        'Securities Account': 1, 'CD Account': 0,
        'Online': 1, 'CreditCard': 1
    }

@pytest.fixture
def cliente_bloqueado_idade():
    return {
        'Age': 20, 'Experience': 0, 'Income': 50,
        'Family': 1, 'Education': 1,
        'Securities Account': 1, 'CD Account': 0,
        'Online': 1, 'CreditCard': 1
    }

@pytest.fixture
def cliente_bloqueado_renda():
    return {
        'Age': 35, 'Experience': 10, 'Income': 20,
        'Family': 2, 'Education': 1,
        'Securities Account': 1, 'CD Account': 0,
        'Online': 1, 'CreditCard': 0
    }

@pytest.fixture
def cliente_bloqueado_relacionamento():
    return {
        'Age': 40, 'Experience': 15, 'Income': 80,
        'Family': 2, 'Education': 2,
        'Securities Account': 0, 'CD Account': 0,
        'Online': 1, 'CreditCard': 0
    }

@pytest.fixture
def cliente_limite_idade():
    return {
        'Age': 21, 'Experience': 0, 'Income': 30,
        'Family': 1, 'Education': 1,
        'Securities Account': 0, 'CD Account': 0,
        'Online': 0, 'CreditCard': 1
    }

@pytest.fixture
def cliente_limite_renda():
    return {
        'Age': 35, 'Experience': 10, 'Income': 25,
        'Family': 2, 'Education': 1,
        'Securities Account': 1, 'CD Account': 0,
        'Online': 1, 'CreditCard': 0
    }


# ================================================================
# TESTES DE SUITABILITY
# ================================================================

class TestSuitability:

    def test_cliente_elegivel_passa(self, cliente_elegivel):
        """Cliente com todos os critérios satisfeitos deve passar."""
        elegivel, motivo = verificar_suitability(cliente_elegivel)
        assert elegivel is True
        assert motivo is None

    def test_bloqueio_por_idade(self, cliente_bloqueado_idade):
        """Cliente com idade < 21 deve ser bloqueado."""
        elegivel, motivo = verificar_suitability(cliente_bloqueado_idade)
        assert elegivel is False
        assert motivo == 'idade_abaixo_21'

    def test_bloqueio_por_renda(self, cliente_bloqueado_renda):
        """Cliente com renda < 25 deve ser bloqueado."""
        elegivel, motivo = verificar_suitability(cliente_bloqueado_renda)
        assert elegivel is False
        assert motivo == 'renda_abaixo_minimo'

    def test_bloqueio_por_relacionamento(self, cliente_bloqueado_relacionamento):
        """Cliente sem nenhum produto deve ser bloqueado."""
        elegivel, motivo = verificar_suitability(cliente_bloqueado_relacionamento)
        assert elegivel is False
        assert motivo == 'sem_relacionamento_bancario'

    def test_limite_idade_exato(self, cliente_limite_idade):
        """Cliente com exatamente 21 anos deve passar."""
        elegivel, motivo = verificar_suitability(cliente_limite_idade)
        assert elegivel is True

    def test_limite_renda_exato(self, cliente_limite_renda):
        """Cliente com renda exatamente 25 deve passar."""
        elegivel, motivo = verificar_suitability(cliente_limite_renda)
        assert elegivel is True

    def test_apenas_credit_card_suficiente(self):
        """Apenas CreditCard=1 deve satisfazer o relacionamento."""
        cliente = {
            'Age': 35, 'Experience': 10, 'Income': 50,
            'Family': 2, 'Education': 1,
            'Securities Account': 0, 'CD Account': 0,
            'Online': 1, 'CreditCard': 1
        }
        elegivel, _ = verificar_suitability(cliente)
        assert elegivel is True

    def test_apenas_cd_account_suficiente(self):
        """Apenas CD Account=1 deve satisfazer o relacionamento."""
        cliente = {
            'Age': 35, 'Experience': 10, 'Income': 50,
            'Family': 2, 'Education': 1,
            'Securities Account': 0, 'CD Account': 1,
            'Online': 1, 'CreditCard': 0
        }
        elegivel, _ = verificar_suitability(cliente)
        assert elegivel is True

    def test_apenas_securities_suficiente(self):
        """Apenas Securities Account=1 deve satisfazer o relacionamento."""
        cliente = {
            'Age': 35, 'Experience': 10, 'Income': 50,
            'Family': 2, 'Education': 1,
            'Securities Account': 1, 'CD Account': 0,
            'Online': 1, 'CreditCard': 0
        }
        elegivel, _ = verificar_suitability(cliente)
        assert elegivel is True


# ================================================================
# TESTES DE RECOMPENSA
# ================================================================

class TestRecompensa:

    def test_conversao_retorna_1(self):
        """Mostrou banner e cliente converteu deve retornar 1.0."""
        assert calcular_recompensa(1, 1) == 1.0

    def test_sem_conversao_retorna_penalidade(self):
        """Mostrou banner e cliente não converteu deve retornar -0.01."""
        assert calcular_recompensa(1, 0) == -0.01

    def test_nao_mostrou_retorna_zero(self):
        """Não mostrou o banner deve retornar 0.0."""
        assert calcular_recompensa(0, 0) == 0.0
        assert calcular_recompensa(0, 1) == 0.0

    def test_recompensa_nao_mostrou_independe_resultado(self):
        """Recompensa de não mostrar deve ser 0 independente do resultado."""
        assert calcular_recompensa(0, 0) == calcular_recompensa(0, 1)


# ================================================================
# TESTES DO BANDIT
# ================================================================

class TestBandit:

    def test_bandit_retorna_0_ou_1(self, cliente_elegivel):
        """Bandit deve retornar apenas 0 ou 1."""
        acao = bandit.predict()
        assert acao in [0, 1]

    def test_bandit_retorna_inteiro(self):
        """Bandit deve retornar valor inteiro."""
        acao = bandit.predict()
        assert isinstance(acao, (int, np.integer))

    def test_partial_fit_nao_quebra(self, cliente_elegivel):
        """partial_fit deve executar sem erro."""
        try:
            bandit.partial_fit(decisions=[1], rewards=[1.0])
            assert True
        except Exception as e:
            pytest.fail(f"partial_fit lançou exceção: {e}")


# ================================================================
# TESTES DO FLUXO COMPLETO
# ================================================================

class TestFluxoCompleto:

    def test_tomar_decisao_bloqueado_retorna_0(self, cliente_bloqueado_idade):
        """tomar_decisao para cliente bloqueado deve retornar 0."""
        acao = tomar_decisao(cliente_bloqueado_idade, bandit)
        assert acao == 0

    def test_tomar_decisao_elegivel_retorna_0_ou_1(self, cliente_elegivel):
        """tomar_decisao para cliente elegível deve retornar 0 ou 1."""
        acao = tomar_decisao(cliente_elegivel, bandit)
        assert acao in [0, 1]

    def test_log_registra_decisao(self, cliente_elegivel):
        """tomar_decisao deve registrar no log de auditoria."""
        tamanho_antes = len(log_auditoria)
        tomar_decisao(cliente_elegivel, bandit)
        assert len(log_auditoria) == tamanho_antes + 1

    def test_log_tem_campos_obrigatorios(self, cliente_elegivel):
        """Registro no log deve ter todos os campos obrigatórios."""
        tomar_decisao(cliente_elegivel, bandit)
        ultimo_registro = log_auditoria[-1]

        campos_obrigatorios = [
            'timestamp', 'age', 'income', 'passou_suitability',
            'acao', 'tipo_decisao', 'recompensa'
        ]
        for campo in campos_obrigatorios:
            assert campo in ultimo_registro, f"Campo '{campo}' ausente no log"

    def test_log_bloqueado_tem_motivo(self, cliente_bloqueado_idade):
        """Registro de cliente bloqueado deve ter motivo_bloqueio preenchido."""
        tomar_decisao(cliente_bloqueado_idade, bandit)
        ultimo_registro = log_auditoria[-1]
        assert ultimo_registro['passou_suitability'] is False
        assert ultimo_registro['motivo_bloqueio'] is not None
        assert ultimo_registro['tipo_decisao'] == 'bloqueado'

    def test_log_elegivel_sem_motivo_bloqueio(self, cliente_elegivel):
        """Registro de cliente elegível não deve ter motivo_bloqueio."""
        tomar_decisao(cliente_elegivel, bandit)
        ultimo_registro = log_auditoria[-1]
        assert ultimo_registro['passou_suitability'] is True
        assert ultimo_registro['motivo_bloqueio'] is None


# ================================================================
# TESTES DE CONTRATO DE DADOS
# ================================================================

class TestContratoDados:

    def test_contexto_tem_todas_variaveis(self, cliente_elegivel):
        """Contexto deve ter as 9 variáveis obrigatórias."""
        variaveis_obrigatorias = [
            'Age', 'Experience', 'Income', 'Family', 'Education',
            'Securities Account', 'CD Account', 'Online', 'CreditCard'
        ]
        for var in variaveis_obrigatorias:
            assert var in cliente_elegivel, f"Variável '{var}' ausente no contexto"

    def test_variaveis_sao_numericas(self, cliente_elegivel):
        """Todas as variáveis do contexto devem ser numéricas."""
        for var, valor in cliente_elegivel.items():
            assert isinstance(valor, (int, float)), \
                f"Variável '{var}' não é numérica: {type(valor)}"

    def test_variaveis_binarias_sao_0_ou_1(self, cliente_elegivel):
        """Variáveis binárias devem ser 0 ou 1."""
        binarias = ['Securities Account', 'CD Account', 'Online', 'CreditCard']
        for var in binarias:
            assert cliente_elegivel[var] in [0, 1], \
                f"Variável binária '{var}' tem valor inválido: {cliente_elegivel[var]}"
