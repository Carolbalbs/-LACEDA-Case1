"""
Constantes e caminhos padrão do pipeline. Nenhuma lógica — só os valores que
os outros módulos compartilham.
"""

from __future__ import annotations

from pathlib import Path

# raiz do projeto: .../[LACEDA]Case1
RAIZ = Path(__file__).resolve().parents[2]
DIR_DADOS = RAIZ / "data" / "raw"
DIR_SAIDA = RAIZ / "output"

CNEFE_PADRAO = DIR_DADOS / "29_BA.csv"
SAIDA_PADRAO = DIR_SAIDA / "resultado_final.csv"
NOME_LOG = "log_execucao.json"

# as 12 colunas do CNEFE que interessam ao pareamento (das 34 do arquivo)
COLUNAS_UTEIS = [
    "COD_UNICO_ENDERECO", "COD_MUNICIPIO", "COD_SETOR", "CEP", "DSC_LOCALIDADE",
    "NOM_TIPO_SEGLOGR", "NOM_TITULO_SEGLOGR", "NOM_SEGLOGR", "NUM_ENDERECO",
    "DSC_MODIFICADOR", "LATITUDE", "LONGITUDE",
]

# papel do campo -> palavras-chave que o identificam na base de busca
PAPEIS = {
    "municipio": ["munic", "cod_mun", "ibge"],
    "cep": ["cep"],
    "logradouro": ["logr", "endereco", "rua", "address"],
    "numero": ["numero", "num", "nro"],
    "bairro": ["bairro", "localidade", "distrito"],
}
PAPEIS_OBRIGATORIOS = {"municipio", "cep", "logradouro"}

EXTENSOES_BUSCA = {".xlsx", ".xls", ".csv"}
PREFIXO_CNEFE = "29_BA"          # arquivo do CNEFE, nunca é a base de busca
PREFIXO_GABARITO = "_gabarito"   # colunas da base sintética, fora da entrega
