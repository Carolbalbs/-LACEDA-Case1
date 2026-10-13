"""
Busca em cascata do setor censitário — Passo 3 do plano de trabalho.

A ideia é tentar regras da mais específica para a mais tolerante, parando na
primeira que resolve. Cada resposta carrega a regra que a produziu, para que a
saída seja auditável.

| nível | chave de busca                                   | confiança |
|-------|--------------------------------------------------|-----------|
| 1     | município + CEP + logradouro + número (exato)    | ALTA      |
| 2     | município + CEP + logradouro (exato)             | ALTA      |
| 3     | município + logradouro + número (exato)          | MEDIA     |
| 4     | município + CEP, logradouro parecido (fuzzy)     | MEDIA     |
| 5     | município + bairro, logradouro parecido (fuzzy)  | BAIXA     |
| 6     | nada bateu                                       | —         |

Dois cuidados que o plano destaca:
  - vários endereços parecidos apontando para o MESMO setor não são
    ambiguidade: a resposta está resolvida;
  - apontando para setores DIFERENTES, a resposta é `AMBIGUO` e o setor fica
    vazio. Melhor assumir que não sabe do que chutar errado.
"""

from __future__ import annotations

from collections import defaultdict

from rapidfuzz import fuzz, process

LIMIAR_FUZZY_CEP = 88     # nível 4: o CEP já restringe muito, pode ser tolerante
LIMIAR_FUZZY_BAIRRO = 92  # nível 5: bloco mais largo, exige mais parecença

STATUS_ENCONTRADO = "ENCONTRADO"
STATUS_AMBIGUO = "AMBIGUO"
STATUS_NAO_ENCONTRADO = "NAO_ENCONTRADO"


class IndiceCNEFE:
    """Índices em memória sobre o recorte do CNEFE já normalizado."""

    def __init__(self, df):
        """`df` precisa ter: n_municipio, n_cep, n_logradouro, n_numero,
        n_bairro, setor_15."""
        self.exato_cep_num = defaultdict(set)   # nível 1
        self.exato_cep = defaultdict(set)       # nível 2
        self.exato_num = defaultdict(set)       # nível 3
        self.bloco_cep = defaultdict(lambda: defaultdict(set))     # nível 4
        self.bloco_bairro = defaultdict(lambda: defaultdict(set))  # nível 5

        colunas = ["n_municipio", "n_cep", "n_logradouro", "n_numero",
                   "n_bairro", "setor_15"]
        for mun, cep, logr, num, bairro, setor in df[colunas].itertuples(index=False):
            if not mun or not logr or not setor:
                continue
            if cep:
                self.exato_cep[(mun, cep, logr)].add(setor)
                self.bloco_cep[(mun, cep)][logr].add(setor)
                if num != "SN":
                    self.exato_cep_num[(mun, cep, logr, num)].add(setor)
            if num != "SN":
                self.exato_num[(mun, logr, num)].add(setor)
            if bairro:
                self.bloco_bairro[(mun, bairro)][logr].add(setor)

        # listas de logradouros por bloco, pré-calculadas para o rapidfuzz
        self._logr_cep = {k: list(v) for k, v in self.bloco_cep.items()}
        self._logr_bairro = {k: list(v) for k, v in self.bloco_bairro.items()}

    def __len__(self):
        return len(self.exato_cep)


def _resolver(setores, regra, score, confianca):
    """Traduz um conjunto de setores candidatos em uma resposta."""
    setores = {s for s in setores if s}
    if not setores:
        return None
    if len(setores) == 1:
        return {
            "setor_censitario_encontrado": next(iter(setores)),
            "status": STATUS_ENCONTRADO,
            "regra": regra,
            "score": score,
            "confianca": confianca,
            "n_setores_candidatos": 1,
            "setores_candidatos": next(iter(setores)),
        }
    return {
        "setor_censitario_encontrado": "",
        "status": STATUS_AMBIGUO,
        "regra": regra,
        "score": score,
        "confianca": confianca,
        "n_setores_candidatos": len(setores),
        "setores_candidatos": "|".join(sorted(setores)),
    }


def _fuzzy(alvo, candidatos, mapa, limiar):
    """Melhor logradouro acima do limiar; devolve (setores, score) ou (None, None)."""
    if not alvo or not candidatos:
        return None, None
    achado = process.extractOne(alvo, candidatos, scorer=fuzz.token_sort_ratio,
                                score_cutoff=limiar)
    if achado is None:
        return None, None
    logr, score, _ = achado
    return mapa[logr], round(float(score), 1)


def buscar_setor(endereco: dict, indice: IndiceCNEFE,
                 limiar_cep: float = LIMIAR_FUZZY_CEP,
                 limiar_bairro: float = LIMIAR_FUZZY_BAIRRO) -> dict:
    """Roda a cascata para um endereço normalizado e devolve a resposta."""
    mun = endereco.get("n_municipio", "")
    cep = endereco.get("n_cep", "")
    logr = endereco.get("n_logradouro", "")
    num = endereco.get("n_numero", "SN")
    bairro = endereco.get("n_bairro", "")

    nao_encontrado = {
        "setor_censitario_encontrado": "",
        "status": STATUS_NAO_ENCONTRADO,
        "regra": "6_NAO_ENCONTRADO",
        "score": None,
        "confianca": "",
        "n_setores_candidatos": 0,
        "setores_candidatos": "",
    }

    if not mun or not logr:
        nao_encontrado["regra"] = "0_CAMPOS_INSUFICIENTES"
        return nao_encontrado

    # nível 1 — município + CEP + logradouro + número
    if cep and num != "SN":
        r = _resolver(indice.exato_cep_num.get((mun, cep, logr, num), set()),
                      "1_EXATO_CEP_LOGR_NUM", 100.0, "ALTA")
        if r:
            return r

    # nível 2 — município + CEP + logradouro
    if cep:
        r = _resolver(indice.exato_cep.get((mun, cep, logr), set()),
                      "2_EXATO_CEP_LOGR", 100.0, "ALTA")
        if r:
            return r

    # nível 3 — município + logradouro + número (sem CEP)
    if num != "SN":
        r = _resolver(indice.exato_num.get((mun, logr, num), set()),
                      "3_EXATO_LOGR_NUM", 100.0, "MEDIA")
        if r:
            return r

    # nível 4 — dentro do CEP, logradouro parecido
    if cep:
        mapa = indice.bloco_cep.get((mun, cep))
        if mapa:
            setores, score = _fuzzy(logr, indice._logr_cep[(mun, cep)], mapa, limiar_cep)
            if setores:
                r = _resolver(setores, "4_FUZZY_CEP", score, "MEDIA")
                if r:
                    return r

    # nível 5 — dentro do bairro, logradouro parecido
    if bairro:
        mapa = indice.bloco_bairro.get((mun, bairro))
        if mapa:
            setores, score = _fuzzy(logr, indice._logr_bairro[(mun, bairro)], mapa,
                                    limiar_bairro)
            if setores:
                r = _resolver(setores, "5_FUZZY_BAIRRO", score, "BAIXA")
                if r:
                    return r

    # nível 6 — nada bateu
    return nao_encontrado


def buscar_lote(df, indice: IndiceCNEFE, **kwargs):
    """Aplica a cascata linha a linha e devolve a lista de respostas."""
    return [buscar_setor(linha, indice, **kwargs)
            for linha in df.to_dict(orient="records")]
