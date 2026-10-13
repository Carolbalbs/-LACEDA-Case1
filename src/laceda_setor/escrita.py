"""
Saída de dados: gravar o resultado e o log de execução. Responsabilidade única —
recebe o que já foi calculado e só persiste em disco.
"""

from __future__ import annotations

import json
from pathlib import Path

import pandas as pd

from .config import NOME_LOG


def salvar_resultado(df: pd.DataFrame, saida: Path) -> Path:
    """Grava o resultado em CSV e, ao lado, a mesma tabela em Parquet."""
    saida = Path(saida)
    saida.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(saida, index=False, encoding="utf-8")
    df.to_parquet(saida.with_suffix(".parquet"), index=False)
    return saida


def salvar_log(log: dict, diretorio: Path, nome: str = NOME_LOG) -> Path:
    """Grava o log da execução em JSON legível."""
    diretorio = Path(diretorio)
    diretorio.mkdir(parents=True, exist_ok=True)
    caminho = diretorio / nome
    caminho.write_text(json.dumps(log, indent=2, ensure_ascii=False))
    return caminho
