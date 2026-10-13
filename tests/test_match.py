"""Testes da cascata — com um CNEFE minúsculo, montado à mão."""

import pandas as pd
import pytest

from laceda_setor import match as mt


def _cnefe(linhas):
    return pd.DataFrame(linhas, columns=["n_municipio", "n_cep", "n_logradouro",
                                         "n_numero", "n_bairro", "setor_15"])


@pytest.fixture
def indice():
    return mt.IndiceCNEFE(_cnefe([
        ("290070", "48030260", "RUA RIO BAIANO", "100", "CENTRO", "290070205000001"),
        ("290070", "48030260", "RUA RIO BAIANO", "102", "CENTRO", "290070205000001"),
        # mesmo logradouro, outro CEP, OUTRO setor -> fonte de ambiguidade sem CEP
        ("290070", "48031000", "RUA RIO BAIANO", "100", "KENNEDY", "290070205000099"),
        ("290070", "48030999", "AVENIDA DOUTOR ABELARDO VELOSO", "SN", "CENTRO",
         "290070205000002"),
        ("290130", "46830000", "POVOADO SAO JOSE", "SN", "ZONA RURAL", "290130205000003"),
    ]))


def test_nivel_1_exato_com_numero(indice):
    r = mt.buscar_setor({"n_municipio": "290070", "n_cep": "48030260",
                         "n_logradouro": "RUA RIO BAIANO", "n_numero": "100"}, indice)
    assert r["status"] == mt.STATUS_ENCONTRADO
    assert r["setor_censitario_encontrado"] == "290070205000001"
    assert r["regra"].startswith("1_")


def test_nivel_2_sem_numero(indice):
    """29% do CNEFE não tem número: precisa existir caminho que o ignore."""
    r = mt.buscar_setor({"n_municipio": "290070", "n_cep": "48030260",
                         "n_logradouro": "RUA RIO BAIANO", "n_numero": "SN"}, indice)
    assert r["status"] == mt.STATUS_ENCONTRADO
    assert r["regra"].startswith("2_")


def test_numeros_diferentes_mesmo_setor_nao_e_ambiguidade(indice):
    """Dois endereços distintos apontando para o MESMO setor: resposta resolvida."""
    r = mt.buscar_setor({"n_municipio": "290070", "n_cep": "48030260",
                         "n_logradouro": "RUA RIO BAIANO", "n_numero": "SN"}, indice)
    assert r["n_setores_candidatos"] == 1


def test_setores_diferentes_viram_ambiguo(indice):
    """Sem CEP, 'RUA RIO BAIANO 100' existe em dois setores -> não chutar."""
    r = mt.buscar_setor({"n_municipio": "290070", "n_cep": "",
                         "n_logradouro": "RUA RIO BAIANO", "n_numero": "100"}, indice)
    assert r["status"] == mt.STATUS_AMBIGUO
    assert r["setor_censitario_encontrado"] == ""
    assert r["n_setores_candidatos"] == 2


def test_nivel_4_fuzzy_dentro_do_cep(indice):
    """Letra faltando no logradouro, mas o CEP ancora a busca."""
    r = mt.buscar_setor({"n_municipio": "290070", "n_cep": "48030260",
                         "n_logradouro": "RUA RIO BAIANNO", "n_numero": "SN"}, indice)
    assert r["status"] == mt.STATUS_ENCONTRADO
    assert r["regra"].startswith("4_")
    assert r["score"] >= mt.LIMIAR_FUZZY_CEP


def test_nivel_5_fuzzy_por_bairro(indice):
    """Sem CEP, o bairro ainda oferece um bloco de busca."""
    r = mt.buscar_setor({"n_municipio": "290130", "n_cep": "",
                         "n_logradouro": "POVOADO SAO JOZE", "n_numero": "SN",
                         "n_bairro": "ZONA RURAL"}, indice)
    assert r["status"] == mt.STATUS_ENCONTRADO
    assert r["regra"].startswith("5_")
    assert r["confianca"] == "BAIXA"


def test_nivel_6_nao_encontrado(indice):
    r = mt.buscar_setor({"n_municipio": "290070", "n_cep": "99999999",
                         "n_logradouro": "RUA QUE NAO EXISTE", "n_numero": "1"}, indice)
    assert r["status"] == mt.STATUS_NAO_ENCONTRADO
    assert r["setor_censitario_encontrado"] == ""


def test_municipio_errado_nao_vaza_resposta(indice):
    """O blocking por município tem de ser estrito."""
    r = mt.buscar_setor({"n_municipio": "290130", "n_cep": "48030260",
                         "n_logradouro": "RUA RIO BAIANO", "n_numero": "100"}, indice)
    assert r["status"] == mt.STATUS_NAO_ENCONTRADO


def test_campos_insuficientes(indice):
    r = mt.buscar_setor({"n_municipio": "", "n_logradouro": ""}, indice)
    assert r["status"] == mt.STATUS_NAO_ENCONTRADO
    assert r["regra"].startswith("0_")
