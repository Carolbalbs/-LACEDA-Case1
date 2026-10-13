"""
Localização do setor censitário de endereços no CNEFE (case CIDACS/LACEDA).

Um módulo por responsabilidade:
    config     — constantes e caminhos padrão
    leitura    — achar e ler CNEFE e base de busca
    colunas    — descobrir o esquema da base de busca
    normalize  — limpeza e padronização dos endereços (passo 2)
    match      — busca em cascata do setor censitário (passo 3)
    pipeline   — ordem dos passos, de ponta a ponta
    relatorio  — agregação dos números da execução
    escrita    — gravação do resultado e do log
    cli        — argumentos de linha de comando e impressão
    base_demo  — base de busca sintética, enquanto a real não chega
"""

from . import match, normalize, pipeline
from .pipeline import Opcoes, Resultado, executar

__all__ = ["match", "normalize", "pipeline", "executar", "Opcoes", "Resultado"]
