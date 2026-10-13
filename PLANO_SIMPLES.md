# Plano de Trabalho (versão enxuta) — Case CIDACS: endereço → setor censitário

**O que entregar:** os 100 endereços da base de busca com uma coluna a mais, `setor_censitario_encontrado`, marcando claramente o que não foi encontrado. Mais código no GitHub e um README.

**Como:** Python + pandas (ou DuckDB) + `rapidfuzz`. Sem Spark, sem Elasticsearch. São 100 consultas — ferramenta pesada aqui só atrapalha o prazo.

---

## Os 5 passos

### 1. Olhar os dados (meio dia)
Baixar as duas bases. Abrir e responder:
- Quais colunas o CNEFE tem de fato e como o código do setor aparece (o exemplo do case tem 15 dígitos: `292740805000123`).
- Que tipos de sujeira existem na base de busca: abreviação (`R.`, `AV`), acento, CEP sem máscara, número `SN`, bairro vazio.

Anotar isso num arquivo. É a especificação do passo 2.

### 2. Limpar os endereços (1 dia) — **a parte que mais importa**
Um arquivo `normalize.py` com as regras, **aplicadas igual nos dois lados** (CNEFE e base de busca). Se limpar diferente, o match não acontece.

- maiúsculas, sem acento, sem pontuação
- `R`/`R.` → `RUA`, `AV` → `AVENIDA`, `ROD` → `RODOVIA`, `PCA` → `PRACA`
- `DR` → `DOUTOR`, `STA` → `SANTA`, `N SRA` → `NOSSA SENHORA`
- CEP: só dígitos, completar com zero à esquerda até 8
- número: `S/N`, `SN`, vazio → tudo vira `SN`
- município: resolver nome ↔ código IBGE

### 3. Procurar o setor (1,5 dia)
Tentar em ordem, parando no primeiro que acerta:

| | Busca por | Resultado |
|---|---|---|
| 1 | município + CEP + logradouro + número (exato) | encontrado |
| 2 | município + CEP + logradouro (exato) | encontrado |
| 3 | município + logradouro + número (exato) | encontrado |
| 4 | município + CEP, logradouro parecido (`rapidfuzz`) | encontrado |
| 5 | município + bairro, logradouro parecido | encontrado (confiança baixa) |
| 6 | nada bateu | **não encontrado** |

Dois cuidados que valem nota:
- **Se vários endereços parecidos apontam para o mesmo setor, está resolvido.** Ambiguidade de endereço não é ambiguidade de resposta — isso salva vários dos 100 casos.
- **Se apontam para setores diferentes, marcar `AMBIGUO` e deixar vazio.** Melhor assumir que não sabe do que chutar errado.

### 4. Gerar a saída (meio dia)
`resultado_final.csv` com as 100 linhas originais intactas + 4 colunas:
- `setor_censitario_encontrado`
- `status` — `ENCONTRADO` / `AMBIGUO` / `NAO_ENCONTRADO`
- `regra` — qual dos 6 níveis resolveu
- `score` — similaridade, quando houve fuzzy

E um resumo curto: quantos encontrados, por qual regra, quantos ficaram de fora.

### 5. Empacotar (meio dia)
- `README.md`: abordagem, como rodar, dependências, **premissas** e **limitações** (o case cobra essas duas).
- `requirements.txt` com versões fixas.
- Alguns testes de `normalize.py` com os casos do próprio enunciado (`RODOVIA BR 101`, `RUA RIO BAIANO` + `SN`).
- Dockerfile simples (opcional, mas é fácil e conta ponto).

---

## Estrutura do repositório

```
.
├── README.md
├── requirements.txt
├── Dockerfile
├── data/           # não commitar as bases; instruções no README
├── src/
│   ├── normalize.py    # limpeza (passo 2)
│   ├── match.py        # busca em cascata (passo 3)
│   └── main.py         # roda tudo de ponta a ponta
├── tests/
└── output/resultado_final.csv
```

Objetivo: o avaliador clonar, rodar **um comando** e obter o mesmo CSV.

---

## Ordem de prioridade

1. Fazer o caminho inteiro funcionar, mesmo tosco — até a regra 1 só, com saída e README.
2. Depois melhorar a limpeza e adicionar as regras 2 a 6.
3. Só então pensar em Docker, métricas extras, refinamento de limiar.

Nunca ficar 3 dias polindo a normalização sem nada rodando ponta a ponta.

---

## Dois pontos a confirmar antes de começar

- O prazo no PDF é **18/05/2026**, data que já passou. Perguntar à comissão qual vale.
- Os links são do SharePoint da Fiocruz e podem pedir login. Se o download automático não funcionar, o código deve rodar a partir dos arquivos locais.
