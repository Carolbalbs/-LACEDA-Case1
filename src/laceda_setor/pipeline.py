"""
Orquestração do pipeline: encadeia leitura -> normalização -> cascata -> saída.

Responsabilidade única: a ordem dos passos. Cada passo em si mora no seu módulo;
aqui não há regra de endereço, SQL nem argparse.
"""

from __future__ import annotations

import time
from dataclasses import dataclass, field
from pathlib import Path

import duckdb
import pandas as pd

from . import colunas as cl
from . import escrita, leitura, relatorio
from . import match as mt
from . import normalize as nz
from .config import CNEFE_PADRAO, DIR_DADOS, PREFIXO_GABARITO, SAIDA_PADRAO


class ErroDePipeline(Exception):
    """Falha prevista de execução (arquivo ausente, esquema incompleto)."""


@dataclass
class Opcoes:
    """Tudo que o pipeline precisa saber para rodar."""
    cnefe: Path = CNEFE_PADRAO
    busca: Path | None = None
    saida: Path = SAIDA_PADRAO
    limiar_cep: float = mt.LIMIAR_FUZZY_CEP
    limiar_bairro: float = mt.LIMIAR_FUZZY_BAIRRO


@dataclass
class Resultado:
    """O que a execução produziu, para quem quiser exibir ou testar."""
    final: pd.DataFrame
    log: dict
    saida: Path
    colunas_detectadas: dict = field(default_factory=dict)


def resolver_base_busca(busca: Path | None, diretorio: Path = DIR_DADOS) -> Path:
    """Usa a base indicada ou procura uma em `data/raw/`."""
    caminho = Path(busca) if busca else leitura.localizar_base_busca(diretorio)
    if caminho is None:
        raise ErroDePipeline(f"base de busca não encontrada em {diretorio} (veja o README)")
    if not caminho.exists():
        raise ErroDePipeline(f"base de busca não encontrada: {caminho}")
    return caminho


def preparar_busca(bruta: pd.DataFrame) -> tuple[pd.DataFrame, dict]:
    """Detecta o esquema da base de busca e devolve a versão normalizada."""
    mapa = cl.mapear_colunas(bruta)
    faltando = cl.papeis_faltando(mapa)
    if faltando:
        raise ErroDePipeline(f"colunas essenciais não detectadas: {faltando}")
    return nz.normalizar_base_busca(bruta, mapa), mapa


def parear(busca: pd.DataFrame, cnefe: pd.DataFrame, opcoes: Opcoes) -> pd.DataFrame:
    """Monta o índice do CNEFE e roda a cascata para cada endereço."""
    indice = mt.IndiceCNEFE(nz.normalizar_cnefe(cnefe))
    return pd.DataFrame(mt.buscar_lote(busca, indice,
                                       limiar_cep=opcoes.limiar_cep,
                                       limiar_bairro=opcoes.limiar_bairro))


def juntar(bruta: pd.DataFrame, respostas: pd.DataFrame) -> pd.DataFrame:
    """Colunas originais da base de busca + resposta, lado a lado."""
    originais = [c for c in bruta.columns if not c.startswith(PREFIXO_GABARITO)]
    return pd.concat([bruta[originais].reset_index(drop=True), respostas], axis=1)


def executar(opcoes: Opcoes, aviso=lambda _: None) -> Resultado:
    """Roda o pipeline inteiro. `aviso` recebe mensagens de progresso."""
    inicio = time.time()

    caminho_busca = resolver_base_busca(opcoes.busca)
    bruta = leitura.ler_busca(caminho_busca)
    busca, mapa = preparar_busca(bruta)
    aviso(f"base de busca: {caminho_busca.name} ({len(bruta)} linhas) | colunas: {mapa}")

    municipios = sorted(set(busca["n_municipio"]) - {""})
    try:
        cnefe = leitura.carregar_cnefe(Path(opcoes.cnefe), municipios, duckdb.connect())
    except FileNotFoundError as erro:
        raise ErroDePipeline(str(erro)) from erro
    aviso(f"recorte do CNEFE: {len(cnefe):,} endereços em {len(municipios)} municípios")

    final = juntar(bruta, parear(busca, cnefe, opcoes))
    saida = escrita.salvar_resultado(final, Path(opcoes.saida))
    log = relatorio.montar_log(final, base_busca=caminho_busca.name,
                               municipios=municipios, enderecos_cnefe=len(cnefe),
                               segundos=time.time() - inicio)
    escrita.salvar_log(log, saida.parent)
    return Resultado(final=final, log=log, saida=saida, colunas_detectadas=mapa)
