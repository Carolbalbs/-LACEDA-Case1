"""
Resumo da execução: transforma o resultado em números. Responsabilidade única —
só agrega e formata; não grava arquivos nem imprime.
"""

from __future__ import annotations

from datetime import datetime

import pandas as pd


def contar(serie: pd.Series) -> dict:
    """Contagem por valor, já convertida para tipos nativos do Python."""
    return {str(k): int(v) for k, v in serie.value_counts().items()}


def montar_log(final: pd.DataFrame, *, base_busca: str, municipios: list[str],
               enderecos_cnefe: int, segundos: float) -> dict:
    """Dicionário com tudo que descreve a execução, pronto para virar JSON."""
    return {
        "executado_em": datetime.now().isoformat(timespec="seconds"),
        "base_busca": base_busca,
        "municipios": municipios,
        "enderecos_cnefe_no_recorte": int(enderecos_cnefe),
        "status": contar(final["status"]),
        "regras": contar(final["regra"]),
        "segundos": round(segundos, 1),
    }


def linhas_resumo(final: pd.DataFrame) -> list[str]:
    """Linhas 'STATUS  n  (x%)' para exibição no terminal."""
    total = len(final) or 1
    return [f"  {chave:<16} {valor:>4}  ({100 * valor / total:.1f}%)"
            for chave, valor in contar(final["status"]).items()]
