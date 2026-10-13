"""
Interface de linha de comando. Responsabilidade única: ler argumentos, chamar o
pipeline e imprimir o resumo.

    python src/main.py                              # usa data/raw/
    python src/main.py --busca minha_base.xlsx      # outra base de busca
    python -m laceda_setor                          # idem, com PYTHONPATH=src
"""

from __future__ import annotations

import argparse
from pathlib import Path

from . import match as mt
from . import relatorio
from .config import CNEFE_PADRAO, SAIDA_PADRAO
from .pipeline import ErroDePipeline, Opcoes, executar


def analisar_argumentos(argv=None) -> Opcoes:
    ap = argparse.ArgumentParser(description="Localiza o setor censitário de cada endereço.")
    ap.add_argument("--cnefe", default=CNEFE_PADRAO, type=Path)
    ap.add_argument("--busca", default=None, type=Path, help="base de busca (.xlsx/.csv)")
    ap.add_argument("--saida", default=SAIDA_PADRAO, type=Path)
    ap.add_argument("--limiar-cep", type=float, default=mt.LIMIAR_FUZZY_CEP)
    ap.add_argument("--limiar-bairro", type=float, default=mt.LIMIAR_FUZZY_BAIRRO)
    args = ap.parse_args(argv)
    return Opcoes(cnefe=args.cnefe, busca=args.busca, saida=args.saida,
                  limiar_cep=args.limiar_cep, limiar_bairro=args.limiar_bairro)


def imprimir_resumo(resultado) -> None:
    print(f"\n{resultado.saida} — {len(resultado.final)} linhas")
    for linha in relatorio.linhas_resumo(resultado.final):
        print(linha)
    print(f"concluído em {resultado.log['segundos']}s")


def main(argv=None) -> None:
    try:
        resultado = executar(analisar_argumentos(argv), aviso=print)
    except ErroDePipeline as erro:
        raise SystemExit(str(erro))
    imprimir_resumo(resultado)


if __name__ == "__main__":
    main()
