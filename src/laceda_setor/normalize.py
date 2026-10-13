"""
Normalização de endereços — Passo 2 do plano de trabalho.

Regra de ouro: as MESMAS funções são aplicadas aos dois lados (CNEFE e base de
busca). Se os lados forem limpos de formas diferentes, o match não acontece.

Decisões ancoradas no reconhecimento do Passo 1 (ver ACHADOS_PASSO1.md):
  - COD_SETOR do CNEFE tem 16 chars e termina em 'P'  -> cortar em 15.
  - COD_MUNICIPIO do CNEFE tem 7 dígitos; a base de busca usa 6 -> juntar por 6.
  - O logradouro do CNEFE vem partido em 3 colunas -> compor antes de comparar.
  - 29% do CNEFE não tem número (NUM_ENDERECO='0' + DSC_MODIFICADOR='SN').
"""

from __future__ import annotations

import re
import unicodedata

# --------------------------------------------------------------------------
# Dicionário de abreviações
# --------------------------------------------------------------------------
# Tipos de logradouro. Inclui os tipos RURAIS (FAZENDA, POVOADO, SITIO), que
# aparecem em mais de 1 milhão de linhas do CNEFE da Bahia.
TIPOS_LOGRADOURO = {
    "R": "RUA", "RU": "RUA",
    "AV": "AVENIDA", "AVEN": "AVENIDA", "AVN": "AVENIDA",
    "ROD": "RODOVIA", "RODV": "RODOVIA",
    "PCA": "PRACA", "PC": "PRACA", "PRC": "PRACA",
    "TV": "TRAVESSA", "TRAV": "TRAVESSA", "TRV": "TRAVESSA",
    "EST": "ESTRADA", "ESTR": "ESTRADA",
    "AL": "ALAMEDA", "ALM": "ALAMEDA",
    "LGO": "LARGO", "LG": "LARGO",
    "BC": "BECO",
    "CJ": "CONJUNTO", "CONJ": "CONJUNTO",
    "LOT": "LOTEAMENTO", "LOTE": "LOTEAMENTO",
    "VL": "VILA",
    "JD": "JARDIM", "JRD": "JARDIM",
    "FAZ": "FAZENDA",
    "POV": "POVOADO", "POVO": "POVOADO",
    "SIT": "SITIO",
    "CAM": "CAMINHO",
    "LAD": "LADEIRA",
    "PQ": "PARQUE",
    "DIST": "DISTRITO",
}

# Títulos e patentes que costumam vir abreviados no meio do nome.
TITULOS = {
    "DR": "DOUTOR", "DRA": "DOUTORA",
    "STA": "SANTA", "STO": "SANTO",
    "PE": "PADRE", "FR": "FREI",
    "PROF": "PROFESSOR", "PROFA": "PROFESSORA",
    "PRES": "PRESIDENTE",
    "GEN": "GENERAL", "CEL": "CORONEL", "MAL": "MARECHAL",
    "CAP": "CAPITAO", "TEN": "TENENTE", "SGT": "SARGENTO",
    "ENG": "ENGENHEIRO",
    "VER": "VEREADOR",
    "DEP": "DEPUTADO", "SEN": "SENADOR", "GOV": "GOVERNADOR",
    "MIN": "MINISTRO", "DES": "DESEMBARGADOR",
    "CMTE": "COMANDANTE",
    "MONS": "MONSENHOR",
}

ABREVIACOES = {**TIPOS_LOGRADOURO, **TITULOS}

# Sequências de mais de um token (aplicadas antes do passo token-a-token).
EXPRESSOES = [
    (r"\bN\s+SRA\b", "NOSSA SENHORA"),
    (r"\bN\s+S\b", "NOSSA SENHORA"),
    (r"\bNSA\s+SRA\b", "NOSSA SENHORA"),
    (r"\bNOSSA\s+SRA\b", "NOSSA SENHORA"),
    (r"\bSRA\s+DE\b", "SENHORA DE"),
    (r"\bS\s+SEBASTIAO\b", "SAO SEBASTIAO"),
    (r"\bSAO\s+JOAO\s+B\b", "SAO JOAO BATISTA"),
]

_MARCAS_SEM_NUMERO = {"", "SN", "S/N", "S N", "SN.", "S/N.", "0",
                      "SEM NUMERO", "SEMNUMERO", "S/NUMERO", "NAO INFORMADO"}

_NAO_ALFANUM = re.compile(r"[^A-Z0-9]+")
_ESPACOS = re.compile(r"\s+")
_DIGITOS = re.compile(r"\d+")


# --------------------------------------------------------------------------
# Blocos elementares
# --------------------------------------------------------------------------
def tirar_acentos(texto: str) -> str:
    """'ANDARAÍ' -> 'ANDARAI'."""
    nfkd = unicodedata.normalize("NFKD", texto)
    return "".join(c for c in nfkd if not unicodedata.combining(c))


def normalizar_texto(valor) -> str:
    """Maiúsculas, sem acento, sem pontuação, espaço simples."""
    if valor is None:
        return ""
    texto = str(valor).strip()
    if texto.lower() in {"nan", "none", "<na>", "null"}:
        return ""
    texto = tirar_acentos(texto).upper()
    texto = _NAO_ALFANUM.sub(" ", texto)
    return _ESPACOS.sub(" ", texto).strip()


def expandir_abreviacoes(texto: str) -> str:
    """'AV DR ABELARDO' -> 'AVENIDA DOUTOR ABELARDO'. Espera texto já normalizado."""
    if not texto:
        return ""
    for padrao, troca in EXPRESSOES:
        texto = re.sub(padrao, troca, texto)
    tokens = [ABREVIACOES.get(t, t) for t in texto.split()]
    return " ".join(tokens)


# --------------------------------------------------------------------------
# Campos do endereço
# --------------------------------------------------------------------------
def normalizar_logradouro(valor) -> str:
    """Pipeline completo de logradouro: texto limpo + abreviações expandidas."""
    return expandir_abreviacoes(normalizar_texto(valor))


def compor_logradouro_cnefe(tipo, titulo, nome) -> str:
    """
    O CNEFE guarda o logradouro em 3 colunas; a base de busca traz tudo junto.
    'AVENIDA' + 'DOUTOR' + 'ABELARDO VELOSO' -> 'AVENIDA DOUTOR ABELARDO VELOSO'.
    """
    partes = [normalizar_texto(p) for p in (tipo, titulo, nome)]
    return expandir_abreviacoes(" ".join(p for p in partes if p))


def normalizar_cep(valor) -> str:
    """Só dígitos, 8 posições com zero à esquerda. CEP inválido vira ''."""
    if valor is None:
        return ""
    digitos = "".join(_DIGITOS.findall(str(valor)))
    if not digitos or len(digitos) > 8:
        return ""
    cep = digitos.zfill(8)
    return "" if cep == "00000000" else cep


def normalizar_numero(valor) -> str:
    """
    'S/N', 'SN', vazio e '0' colapsam para o literal 'SN' — o mesmo que o CNEFE
    usa em 29% das linhas. '123-A' vira '123' (o sufixo não ajuda no match).
    """
    texto = normalizar_texto(valor)
    if texto in _MARCAS_SEM_NUMERO:
        return "SN"
    digitos = _DIGITOS.findall(texto)
    if not digitos:
        return "SN"
    numero = digitos[0].lstrip("0")
    return numero if numero else "SN"


def normalizar_municipio(valor) -> str:
    """
    Reduz a 6 dígitos — o denominador comum entre as duas bases.
    CNEFE '2900702' (7 dígitos, com DV) e busca '290070' (6) viram '290070'.
    """
    if valor is None:
        return ""
    digitos = "".join(_DIGITOS.findall(str(valor)))
    if len(digitos) >= 7:
        return digitos[:6]
    return digitos.zfill(6) if digitos else ""


def normalizar_setor(valor) -> str:
    """'290070220000001P' -> '290070220000001' (15 dígitos, formato do enunciado)."""
    if valor is None:
        return ""
    texto = str(valor).strip().upper()
    if texto.endswith("P"):
        texto = texto[:-1]
    return texto if texto.isdigit() and len(texto) == 15 else texto


def normalizar_bairro(valor) -> str:
    """Bairro/localidade: mesmo tratamento do logradouro, sem tipo de via."""
    return expandir_abreviacoes(normalizar_texto(valor))


# --------------------------------------------------------------------------
# Aplicação em lote (pandas)
# --------------------------------------------------------------------------
def normalizar_base_busca(df, colunas: dict):
    """
    Acrescenta ao DataFrame da base de busca as colunas `n_*` normalizadas.
    `colunas` mapeia papel -> nome real da coluna, ex.:
        {'municipio': 'consulta_municipio', 'cep': 'consulta_cep', ...}
    """
    out = df.copy()
    out["n_municipio"] = out[colunas["municipio"]].map(normalizar_municipio)
    out["n_cep"] = out[colunas["cep"]].map(normalizar_cep)
    out["n_logradouro"] = out[colunas["logradouro"]].map(normalizar_logradouro)
    out["n_numero"] = (out[colunas["numero"]].map(normalizar_numero)
                       if colunas.get("numero") else "SN")
    out["n_bairro"] = (out[colunas["bairro"]].map(normalizar_bairro)
                       if colunas.get("bairro") else "")
    return out


def aplicar_em_unicos(serie, funcao):
    """
    Aplica `funcao` só aos valores distintos e repropaga via `map`.

    O CNEFE tem milhões de linhas mas poucos valores distintos por coluna
    (ex.: ~30 mil logradouros em um recorte de 1,5 milhão de endereços).
    Normalizar o distinto e repropagar é uma ordem de grandeza mais rápido.
    """
    unicos = serie.astype("string").fillna("").unique()
    tabela = {v: funcao(v) for v in unicos}
    return serie.astype("string").fillna("").map(tabela)


def normalizar_cnefe(df):
    """Acrescenta as colunas `n_*` e `setor_15` ao recorte do CNEFE."""
    out = df.copy()
    out["n_municipio"] = aplicar_em_unicos(out["COD_MUNICIPIO"], normalizar_municipio)
    out["setor_15"] = aplicar_em_unicos(out["COD_SETOR"], normalizar_setor)
    out["n_cep"] = aplicar_em_unicos(out["CEP"], normalizar_cep)
    out["n_numero"] = aplicar_em_unicos(out["NUM_ENDERECO"], normalizar_numero)
    out["n_bairro"] = aplicar_em_unicos(out["DSC_LOCALIDADE"], normalizar_bairro)

    # logradouro depende de 3 colunas: deduplica a tripla antes de compor
    tipo = out["NOM_TIPO_SEGLOGR"].astype("string").fillna("")
    titulo = out["NOM_TITULO_SEGLOGR"].astype("string").fillna("")
    nome = out["NOM_SEGLOGR"].astype("string").fillna("")
    chave = tipo + "\x1f" + titulo + "\x1f" + nome
    tabela = {k: compor_logradouro_cnefe(*k.split("\x1f")) for k in chave.unique()}
    out["n_logradouro"] = chave.map(tabela)
    return out
