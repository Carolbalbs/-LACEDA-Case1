"""Testes da normalização — os casos vêm do enunciado e dos achados do Passo 1."""

import pytest

from laceda_setor import normalize as nz


@pytest.mark.parametrize("entrada,esperado", [
    ("R. Rio Baiano", "RUA RIO BAIANO"),            # caso do enunciado
    ("RUA RIO BAIANO", "RUA RIO BAIANO"),
    ("Rodovia BR 101", "RODOVIA BR 101"),           # caso do enunciado
    ("ROD BR 101", "RODOVIA BR 101"),
    ("AV DR ABELARDO VELOSO", "AVENIDA DOUTOR ABELARDO VELOSO"),
    ("Pça N Sra da Conceição", "PRACA NOSSA SENHORA DA CONCEICAO"),
    ("estr. do coco", "ESTRADA DO COCO"),
    ("Faz. Boa Vista", "FAZENDA BOA VISTA"),        # tipo rural: 665 mil linhas no CNEFE
    ("POV. SAO JOSE", "POVOADO SAO JOSE"),
    ("  rua   das   flores  ", "RUA DAS FLORES"),
    ("", ""),
    (None, ""),
])
def test_logradouro(entrada, esperado):
    assert nz.normalizar_logradouro(entrada) == esperado


@pytest.mark.parametrize("entrada,esperado", [
    ("48030-260", "48030260"),
    ("48030260", "48030260"),
    (48030260, "48030260"),
    ("8030260", "08030260"),      # zero à esquerda comido pelo Excel
    ("", ""),
    (None, ""),
    ("00000000", ""),             # CEP inválido
    ("123456789", ""),            # dígitos demais
])
def test_cep(entrada, esperado):
    assert nz.normalizar_cep(entrada) == esperado


@pytest.mark.parametrize("entrada", ["S/N", "SN", "s/n", "", None, 0, "0", "SEM NUMERO"])
def test_sem_numero(entrada):
    assert nz.normalizar_numero(entrada) == "SN"


@pytest.mark.parametrize("entrada,esperado", [
    ("123", "123"), ("0045", "45"), ("123-A", "123"), ("123 FUNDOS", "123"),
])
def test_numero(entrada, esperado):
    assert nz.normalizar_numero(entrada) == esperado


def test_municipio_concilia_6_e_7_digitos():
    """O achado central do Passo 1: CNEFE usa 7 dígitos, a base de busca usa 6."""
    assert nz.normalizar_municipio("2900702") == nz.normalizar_municipio("290070") == "290070"
    assert nz.normalizar_municipio("2901304") == nz.normalizar_municipio("290130") == "290130"


def test_setor_perde_o_sufixo_P():
    """100% das 9 milhões de linhas do CNEFE têm 16 chars terminando em P."""
    assert nz.normalizar_setor("290070220000001P") == "290070220000001"
    assert len(nz.normalizar_setor("290070220000001P")) == 15


def test_composicao_do_logradouro_do_cnefe():
    """O CNEFE guarda o logradouro em 3 colunas; a base de busca, em uma só."""
    assert (nz.compor_logradouro_cnefe("AVENIDA", "DOUTOR", "ABELARDO VELOSO")
            == "AVENIDA DOUTOR ABELARDO VELOSO")
    assert nz.compor_logradouro_cnefe("RUA", "", "DAS FLORES") == "RUA DAS FLORES"
    assert nz.compor_logradouro_cnefe("RUA", None, "DAS FLORES") == "RUA DAS FLORES"


def test_os_dois_lados_convergem():
    """A regra de ouro: o mesmo endereço escrito de formas diferentes colapsa."""
    lado_busca = nz.normalizar_logradouro("Av. Dr. Abelardo Veloso")
    lado_cnefe = nz.compor_logradouro_cnefe("AVENIDA", "DOUTOR", "ABELARDO VELOSO")
    assert lado_busca == lado_cnefe
