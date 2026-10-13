"""
Gerador de uma base de busca SINTÉTICA, usada só enquanto a base real
(`data/raw/base_busca.xlsx`, 100 endereços, protegida por login no SharePoint)
não está disponível.

Serve para dois fins:
  - permitir rodar o pipeline de ponta a ponta antes de a base real chegar;
  - fornecer gabarito: como as linhas saem do próprio CNEFE, o setor correto é
    conhecido e dá para medir acurácia da cascata.

NÃO faz parte da entrega. Quando `base_busca.xlsx` existir, o notebook usa a
base real e ignora este módulo.
"""

from __future__ import annotations

import random

# sujeira injetada de propósito, espelhando o que o enunciado descreve
_ABREVIAR = {"RUA": "R.", "AVENIDA": "AV", "RODOVIA": "ROD", "PRACA": "PÇA",
             "TRAVESSA": "TV", "ESTRADA": "EST", "DOUTOR": "DR",
             "SANTA": "STA", "SANTO": "STO", "FAZENDA": "FAZ",
             "POVOADO": "POV", "NOSSA SENHORA": "N SRA"}
_ACENTOS = {"A": "Á", "E": "É", "I": "Í", "O": "Ó", "U": "Ú", "C": "Ç"}


def _abreviar(texto, rng):
    for cheio, curto in _ABREVIAR.items():
        if texto.startswith(cheio + " ") and rng.random() < 0.8:
            return curto + texto[len(cheio):]
    return texto


def _acentuar(texto, rng):
    saida = []
    trocou = False
    for ch in texto:
        if not trocou and ch in _ACENTOS and rng.random() < 0.15:
            saida.append(_ACENTOS[ch])
            trocou = True
        else:
            saida.append(ch)
    return "".join(saida)


def _errar_letra(texto, rng):
    if len(texto) < 6:
        return texto
    i = rng.randrange(3, len(texto) - 1)
    return texto[:i] + texto[i + 1:]       # some uma letra


def gerar(df_cnefe, n=100, semente=42):
    """Sorteia `n` endereços do CNEFE e devolve um DataFrame sujo + gabarito."""
    import pandas as pd

    rng = random.Random(semente)
    amostra = df_cnefe.sample(n=n, random_state=semente).reset_index(drop=True)

    linhas = []
    for i, r in amostra.iterrows():
        logr = r["n_logradouro"]
        dado = rng.random()
        if dado < 0.35:
            logr = _abreviar(logr, rng)
        if dado > 0.75:
            logr = _acentuar(logr, rng)
        if 0.90 < dado:
            logr = _errar_letra(logr, rng)
        if rng.random() < 0.4:
            logr = logr.title()

        cep = r["n_cep"]
        d = rng.random()
        if d < 0.25 and cep:
            cep = f"{cep[:5]}-{cep[5:]}"        # com máscara
        elif d < 0.35 and cep:
            cep = str(int(cep))                  # zero à esquerda comido pelo Excel
        elif d < 0.42:
            cep = ""                             # faltando

        num = r["n_numero"]
        if num == "SN":
            num = rng.choice(["S/N", "SN", "", "s/n"])

        bairro = r["n_bairro"]
        if rng.random() < 0.3:
            bairro = ""

        linhas.append({
            "id_consulta": i + 1,
            "consulta_municipio": r["n_municipio"],       # 6 dígitos, como no enunciado
            "consulta_cep": cep,
            "consulta_logradouro": logr,
            "consulta_numero": num,
            "consulta_bairro": bairro,
            "_gabarito_setor": r["setor_15"],             # só para avaliação
        })
    return pd.DataFrame(linhas)
