"""
Descoberta do esquema da base de busca: associa cada papel do endereço
(município, CEP, logradouro, ...) ao nome real da coluna recebida.

Responsabilidade única: interpretar nomes de coluna. Não lê nem escreve nada.
"""

from __future__ import annotations

from .config import PAPEIS, PAPEIS_OBRIGATORIOS


def mapear_colunas(df, papeis: dict | None = None) -> dict:
    """Associa papel -> nome real da coluna da base de busca, por palavra-chave."""
    papeis = papeis or PAPEIS
    mapa: dict[str, str] = {}
    for papel, termos in papeis.items():
        for coluna in df.columns:
            if any(t in coluna.lower() for t in termos) and coluna not in mapa.values():
                mapa[papel] = coluna
                break
    return mapa


def papeis_faltando(mapa: dict) -> set:
    """Papéis essenciais que não foram encontrados no cabeçalho."""
    return PAPEIS_OBRIGATORIOS - set(mapa)
