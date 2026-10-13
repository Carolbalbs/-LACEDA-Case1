"""
Entrada de dados: achar e ler os arquivos. Responsabilidade única — nada aqui
normaliza, pareia ou escreve.
"""

from __future__ import annotations

from pathlib import Path

import pandas as pd

from .config import COLUNAS_UTEIS, DIR_DADOS, EXTENSOES_BUSCA, PREFIXO_CNEFE


def localizar_base_busca(diretorio: Path = DIR_DADOS) -> Path | None:
    """Primeiro arquivo tabular de `data/raw/` que não seja o CNEFE."""
    for caminho in sorted(diretorio.glob("*")):
        if caminho.suffix.lower() in EXTENSOES_BUSCA and PREFIXO_CNEFE not in caminho.name:
            return caminho
    return None


def ler_busca(caminho: Path) -> pd.DataFrame:
    """Lê a base de busca (.xlsx/.xls/.csv) inteira como texto."""
    if caminho.suffix.lower() == ".csv":
        return pd.read_csv(caminho, dtype=str, sep=None, engine="python")
    return pd.read_excel(caminho, dtype=str)


def carregar_cnefe(csv: Path, municipios: list[str], con) -> pd.DataFrame:
    """
    Lê do CSV só os municípios que aparecem na base de busca (blocking).

    O DuckDB varre o arquivo de 1,46 GB e devolve apenas o recorte (~13s). Não há
    camada intermediária em disco: a base original é lida uma vez por execução e o
    resto do pipeline acontece em memória.

    `all_varchar=true` é obrigatório — zeros à esquerda de CEP, setor e código de
    município são significativos.
    """
    if not Path(csv).exists():
        raise FileNotFoundError(f"CNEFE não encontrado em {csv} (veja o README)")
    lista = ", ".join(f"'{m}'" for m in municipios)
    return con.execute(f"""
        SELECT {', '.join(COLUNAS_UTEIS)}
        FROM read_csv_auto('{csv}', delim=';', header=true, all_varchar=true)
        WHERE LEFT(COD_MUNICIPIO, 6) IN ({lista})
    """).df()
