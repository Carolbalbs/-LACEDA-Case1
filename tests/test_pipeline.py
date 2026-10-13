"""Testes das peças de orquestração: esquema, junção e escolha da base de busca."""

import pandas as pd
import pytest

from laceda_setor import colunas as cl
from laceda_setor import pipeline as pl


def test_mapeia_colunas_do_enunciado():
    df = pd.DataFrame(columns=["id_consulta", "consulta_municipio", "consulta_cep",
                               "consulta_logradouro", "consulta_numero", "consulta_bairro"])
    assert cl.mapear_colunas(df) == {
        "municipio": "consulta_municipio",
        "cep": "consulta_cep",
        "logradouro": "consulta_logradouro",
        "numero": "consulta_numero",
        "bairro": "consulta_bairro",
    }
    assert cl.papeis_faltando(cl.mapear_colunas(df)) == set()


def test_acusa_papel_essencial_ausente():
    df = pd.DataFrame(columns=["municipio_ibge", "bairro"])
    assert cl.papeis_faltando(cl.mapear_colunas(df)) == {"cep", "logradouro"}


def test_preparar_busca_sem_logradouro_falha():
    df = pd.DataFrame({"cod_municipio": ["290070"], "cep": ["40000000"]})
    with pytest.raises(pl.ErroDePipeline):
        pl.preparar_busca(df)


def test_juntar_descarta_colunas_de_gabarito():
    bruta = pd.DataFrame({"id": [1], "consulta_cep": ["40000000"], "_gabarito_setor": ["x"]})
    respostas = pd.DataFrame({"status": ["ENCONTRADO"]})
    assert list(pl.juntar(bruta, respostas).columns) == ["id", "consulta_cep", "status"]


def test_resolver_base_busca_ignora_o_cnefe(tmp_path):
    (tmp_path / "29_BA.csv").touch()
    (tmp_path / "base_busca.xlsx").touch()
    assert pl.resolver_base_busca(None, tmp_path).name == "base_busca.xlsx"


def test_resolver_base_busca_sem_arquivo(tmp_path):
    with pytest.raises(pl.ErroDePipeline):
        pl.resolver_base_busca(None, tmp_path)
