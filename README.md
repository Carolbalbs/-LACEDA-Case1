# Localização de setor censitário a partir de endereços — CNEFE Bahia

Dado um conjunto de endereços com qualidade variável, encontra na base CNEFE da Bahia
(9.047.296 endereços) o **setor censitário** correspondente a cada um, distinguindo
explicitamente os casos encontrados, ambíguos e não encontrados.

## Abordagem

Pareamento determinístico em cascata, com recurso a similaridade textual quando a escrita não
bate exatamente. Três etapas:

1. **Normalização idêntica dos dois lados.** O mesmo código limpa o CNEFE e a base de busca:
   maiúsculas sem acento nem pontuação, abreviações expandidas (`R.`→`RUA`, `AV`→`AVENIDA`,
   `DR`→`DOUTOR`, e também os tipos rurais `FAZ`→`FAZENDA`, `POV`→`POVOADO`), CEP reduzido a 8
   dígitos com zero à esquerda, `S/N`/vazio/`0` colapsados em `SN`. Limpar os dois lados de
   formas diferentes é o erro que impede qualquer match.

2. **Blocking por município.** Só os municípios presentes na base de busca são carregados do
   CNEFE. Reduz o espaço de comparação em ordens de grandeza e dispensa Spark.

   O CSV de 1,46 GB é lido direto, uma vez por execução, sem camada intermediária em disco.
   Converter para Parquet economizaria ~9 s por execução e custaria ~12 s de conversão: não se
   paga, e criaria um cache a manter. O recorte (~1,5 milhão de endereços) segue em memória
   daí em diante.

3. **Busca em cascata**, do mais específico ao mais tolerante, parando no primeiro acerto:

   | nível | chave | confiança |
   |---|---|---|
   | 1 | município + CEP + logradouro + número (exato) | ALTA |
   | 2 | município + CEP + logradouro (exato) | ALTA |
   | 3 | município + logradouro + número (exato) | MEDIA |
   | 4 | município + CEP, logradouro parecido (`rapidfuzz` ≥ 88) | MEDIA |
   | 5 | município + bairro, logradouro parecido (≥ 92) | BAIXA |
   | 6 | nada bateu → `NAO_ENCONTRADO` | — |

   Quando vários endereços candidatos apontam para o **mesmo** setor, a resposta está resolvida.
   Quando apontam para setores **diferentes**, o status é `AMBIGUO` e o setor fica vazio — os
   candidatos ficam registrados em `setores_candidatos`, para auditoria.

A cascata existe porque o poder discriminante do CEP varia muito: 60% dos CEPs da Bahia cobrem
um único setor, mas há CEPs genéricos de município pequeno que cobrem dezenas (`46830000`,
Andaraí: 8.642 endereços em 38 setores). Nenhuma regra única resolve os dois casos.

## Como executar

```bash
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
```

Coloque as duas bases em `data/raw/` (não são versionadas):

| arquivo | origem |
|---|---|
| `29_BA.csv` | CNEFE BA — `ftp.ibge.gov.br` → Censo 2022 → Arquivos_CNEFE → CSV → UF → `29_BA.zip` |
| `base_busca.xlsx` | SharePoint da Fiocruz (link no enunciado; **exige login**) |

Depois:

```bash
python src/main.py
```

Roda em menos de um minuto. Saída em `output/resultado_final.csv` (+ `.parquet`) e
`output/log_execucao.json`.

Opções: `--busca OUTRA_BASE.xlsx`, `--saida caminho.csv`, `--limiar-cep 85`, `--limiar-bairro 95`.

### Docker

```bash
docker build -t cidacs-setor .
docker run --rm -v "$PWD/data:/app/data" -v "$PWD/output:/app/output" cidacs-setor
```

### Testes

```bash
python -m pytest tests/ -q
```

## Saída

As colunas originais da base de busca, intactas, mais:

| coluna | conteúdo |
|---|---|
| `setor_censitario_encontrado` | código de 15 dígitos; **vazio** quando não resolvido |
| `status` | `ENCONTRADO` / `AMBIGUO` / `NAO_ENCONTRADO` |
| `regra` | qual dos 6 níveis resolveu |
| `score` | similaridade (100 nos níveis exatos) |
| `confianca` | ALTA / MEDIA / BAIXA |
| `n_setores_candidatos`, `setores_candidatos` | o que a busca viu nos casos ambíguos |

## Estrutura

```
├── src/
│   ├── main.py                # atalho: `python src/main.py`
│   └── laceda_setor/          # o pacote — um módulo por responsabilidade
│       ├── config.py          # constantes e caminhos padrão
│       ├── leitura.py         # achar e ler CNEFE e base de busca
│       ├── colunas.py         # descobrir o esquema da base de busca
│       ├── normalize.py       # limpeza, aplicada igual aos dois lados
│       ├── match.py           # cascata de 6 níveis
│       ├── pipeline.py        # ordem dos passos, de ponta a ponta
│       ├── relatorio.py       # números da execução
│       ├── escrita.py         # grava resultado e log
│       ├── cli.py             # argumentos e impressão
│       └── base_demo.py       # base sintética (enquanto a real não está disponível)
├── tests/                     # pytest
├── notebooks/
│   ├── 01_analise_exploratoria.ipynb
│   └── 02_pipeline_plano_simples.ipynb
├── data/raw/          # bases de entrada (não versionadas)
└── output/            # resultado + logs
```

## Premissas

- **Município é bloco obrigatório.** Nenhuma resposta é dada fora do município informado na
  consulta. Se o município vier errado na entrada, o endereço fica `NAO_ENCONTRADO`.
- **O código de município da base de busca tem 6 dígitos e o do CNEFE tem 7** (o 7º é o
  verificador). A junção é feita pelos 6 primeiros.
- **`COD_SETOR` do CNEFE é cortado em 15 dígitos**, removendo o sufixo `P` presente em 100%
  das linhas, para corresponder ao formato do enunciado.
- **Ambiguidade não é resolvida por desempate.** Preferiu-se devolver vazio com os candidatos
  registrados a escolher um setor por critério arbitrário (frequência, primeiro encontrado).
- **Todos os campos são lidos como texto**, porque zeros à esquerda em CEP, setor e município
  são significativos.
- **O exemplo de saída do enunciado é ilustrativo.** Os setores `292740805000123` e
  `291230605000456` não existem no CNEFE (`2912306` nem é município válido da Bahia) — o
  exemplo define o formato, não um gabarito.

## Limitações conhecidas

- **Sem geocodificação.** O CNEFE traz latitude e longitude, mas a solução não usa busca
  espacial. Um endereço cuja grafia divergiu demais não é recuperado por proximidade
  geográfica, ainda que o ponto estivesse disponível.
- **Depende do município estar correto.** Não há tentativa de inferir o município a partir do
  CEP quando os dois se contradizem.
- **Limiares de similaridade são fixos** (88 e 92), calibrados por inspeção e não por uma base
  rotulada. O efeito de alterá-los está medido na seção 3.4 do Notebook 2.
- **O fuzzy compara só o logradouro**, dentro de um bloco de CEP ou bairro. Não há pontuação
  combinada entre campos (por exemplo, logradouro parecido + número exato valendo mais).
- **Endereços fora do cadastro não têm como ser resolvidos.** O CNEFE é de 2022; endereços
  novos ou informais simplesmente não constam, e o resultado correto para eles é
  `NAO_ENCONTRADO`.
- **Apenas a Bahia.** O recorte carregado é `29_BA`; outros estados exigiriam baixar os
  arquivos correspondentes.
- **Validado contra base sintética.** Enquanto a base de busca real não esteve disponível, a
  acurácia foi medida contra endereços sorteados do próprio CNEFE com sujeira injetada — um
  cenário otimista, já que todo endereço existe por construção.
