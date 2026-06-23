"""
utils.py
--------
Funcoes auxiliares para carregar e tratar os dados usados no dashboard de Insights.
Manter a logica de dados separada da interface deixa o codigo mais facil de entender.
"""

import os
import re
from collections import Counter

import numpy as np
import pandas as pd
import streamlit as st


# 1. Pega a pasta onde utils.py está (Dashboard)
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

# 2. Volta uma pasta ("..") e entra na pasta correta onde estão os CSVs
PASTA_DADOS = os.path.abspath(
    os.path.join(
        BASE_DIR, 
        "..", 
        "Geracao de dados e analise de sentimentos", 
        "output_csv"
    )
)

# Semente fixa: garante que os dados simulados sejam sempre os mesmos a cada execucao
SEMENTE_SIMULACAO = 42


import os
import pandas as pd


def _ler_csv(nome_arquivo):
    # Usa a constante PASTA_DADOS definida no topo do arquivo
    caminho = os.path.join(PASTA_DADOS, nome_arquivo)

    # Abre o arquivo com a codificação correta
    return pd.read_csv(caminho, encoding="utf-8-sig")


# ------------------------------------------------------------------
# PERFIL DEMOGRAFICO SIMULADO
# ------------------------------------------------------------------
# A base original NAO possui idade, genero, escolaridade nem o
# municipio/estado de cada usuario -- apenas a lista de regioes,
# estados e municipios do Brasil, sem nenhuma ligacao com user_id.
#
# Para permitir a analise de "Perfil dos Participantes" (que e parte
# do modulo de Insights), esses atributos sao SIMULADOS de forma
# determinística (sempre a mesma seed) e proporcoes plausiveis.
# Em nenhum momento esses dados sao tratados como reais na interface.
def gerar_perfil_simulado(user_ids: pd.Series, municipios: pd.DataFrame) -> pd.DataFrame:
    """Gera um perfil demografico simulado (1 linha por usuario)."""
    ids_unicos = pd.Series(sorted(user_ids.dropna().unique()))
    rng = np.random.default_rng(SEMENTE_SIMULACAO)

    faixas_etarias = ["18-25", "26-35", "36-45", "46-60", "60+"]
    peso_faixas = [0.18, 0.30, 0.24, 0.20, 0.08]

    generos = ["Feminino", "Masculino", "Outro / Prefere não dizer"]
    peso_generos = [0.51, 0.47, 0.02]

    escolaridades = ["Fundamental", "Médio", "Superior", "Pós-graduação"]
    peso_escolaridades = [0.15, 0.40, 0.32, 0.13]

    perfil = pd.DataFrame(
        {
            "user_id": ids_unicos,
            "faixa_etaria": rng.choice(faixas_etarias, size=len(ids_unicos), p=peso_faixas),
            "genero": rng.choice(generos, size=len(ids_unicos), p=peso_generos),
            "escolaridade": rng.choice(
                escolaridades, size=len(ids_unicos), p=peso_escolaridades
            ),
        }
    )

    municipios_validos = municipios.dropna(subset=["municipio", "estado", "regiao"]).reset_index(
        drop=True
    )
    idx_municipio = rng.integers(0, len(municipios_validos), size=len(ids_unicos))
    sorteio = municipios_validos.iloc[idx_municipio].reset_index(drop=True)
    perfil["municipio"] = sorteio["municipio"].values
    perfil["estado"] = sorteio["estado"].values
    perfil["regiao"] = sorteio["regiao"].values

    # Ordena as categorias para os graficos saírem sempre na mesma ordem
    perfil["faixa_etaria"] = pd.Categorical(
        perfil["faixa_etaria"], categories=faixas_etarias, ordered=True
    )

    return perfil


@st.cache_data(show_spinner=False)
def carregar_dados() -> dict:
    """
    Carrega todos os CSVs, faz a limpeza basica, gera o perfil simulado dos
    participantes e devolve um dicionario de DataFrames prontos para uso.
    O resultado fica em cache para o dashboard abrir mais rapido.
    """
    comentarios = _ler_csv("comment.csv")
    sentimentos = _ler_csv("comment_sentimento.csv")
    votos_comentario = _ler_csv("comment_vote.csv")
    votos_proposta = _ler_csv("proposal_vote.csv")
    apoios = _ler_csv("proposal_support.csv")
    compartilhamentos = _ler_csv("proposal_share.csv")
    regioes = _ler_csv("region.csv")
    estados = _ler_csv("state.csv")
    municipios = _ler_csv("municipality.csv")

    # --- Converter colunas de data para o tipo correto ---
    for df, coluna in [
        (comentarios, "created_at"),
        (sentimentos, "created_at"),
        (votos_comentario, "created_at"),
        (votos_proposta, "created_at"),
        (apoios, "created_at"),
        (compartilhamentos, "shared_at"),
    ]:
        df[coluna] = pd.to_datetime(df[coluna], errors="coerce")

    # --- Padronizar nome da coluna de data dos compartilhamentos ---
    compartilhamentos = compartilhamentos.rename(columns={"shared_at": "created_at"})

    # --- Tratar a coluna de emocao (pode ter mais de uma separada por "|") ---
    sentimentos["emocao"] = sentimentos["emocao"].fillna("Sem conteudo")
    sentimentos["emocao_principal"] = (
        sentimentos["emocao"].astype(str).str.split("|").str[0].str.strip()
    )

    # --- Garantir que numeros sejam numeros ---
    sentimentos["confianca"] = pd.to_numeric(sentimentos["confianca"], errors="coerce").fillna(0)
    sentimentos["aux_likes_comentario"] = pd.to_numeric(
        sentimentos["aux_likes_comentario"], errors="coerce"
    ).fillna(0)
    sentimentos["aux_respostas"] = pd.to_numeric(
        sentimentos["aux_respostas"], errors="coerce"
    ).fillna(0)

    # --- Montar a hierarquia geografica (regiao -> estado -> municipio) ---
    estados_geo = estados.merge(
        regioes.rename(columns={"name": "regiao"}),
        on="region_id",
        how="left",
    ).rename(columns={"name": "estado"})

    municipios_geo = municipios.rename(columns={"name": "municipio"}).merge(
        estados_geo[["state_id", "estado", "regiao"]],
        on="state_id",
        how="left",
    )

    # --- Gerar o perfil demografico SIMULADO para todos os participantes ---
    todos_user_ids = pd.concat(
        [
            comentarios["user_id"],
            votos_comentario["user_id"],
            votos_proposta["user_id"],
            apoios["user_id"],
            compartilhamentos["user_id"],
        ],
        ignore_index=True,
    )
    perfil = gerar_perfil_simulado(todos_user_ids, municipios_geo)

    # Junta o perfil simulado aos comentarios/sentimentos (permite cruzar
    # sentimento x faixa etaria, regiao, genero e escolaridade)
    sentimentos = sentimentos.merge(perfil, on="user_id", how="left")

    return {
        "comentarios": comentarios,
        "sentimentos": sentimentos,
        "votos_comentario": votos_comentario,
        "votos_proposta": votos_proposta,
        "apoios": apoios,
        "compartilhamentos": compartilhamentos,
        "regioes": regioes,
        "estados": estados_geo,
        "municipios": municipios_geo,
        "perfil": perfil,
        "participantes_ids": sorted(todos_user_ids.dropna().unique().tolist()),
    }


def formatar_numero(valor: float) -> str:
    """Formata numeros grandes no padrao brasileiro (ex: 1.234)."""
    try:
        return f"{int(valor):,}".replace(",", ".")
    except (ValueError, TypeError):
        return str(valor)


def formatar_tempo_discussao(data_inicio, data_fim) -> str:
    """Formata o intervalo entre duas datas como 'X meses' / 'X anos e Y meses' etc."""
    if pd.isna(data_inicio) or pd.isna(data_fim):
        return "—"

    dias = (data_fim - data_inicio).days
    if dias < 0:
        dias = 0

    if dias < 30:
        return f"{dias} dia{'s' if dias != 1 else ''}"

    meses = dias // 30
    if meses < 12:
        return f"{meses} mes{'es' if meses != 1 else ''}"

    anos = meses // 12
    meses_resto = meses % 12
    texto = f"{anos} ano{'s' if anos != 1 else ''}"
    if meses_resto:
        texto += f" e {meses_resto} mes{'es' if meses_resto != 1 else ''}"
    return texto


# ------------------------------------------------------------------
# EXTRACAO DE TEMAS (ranking de palavras mais citadas nos comentarios)
# ------------------------------------------------------------------
STOPWORDS_PT = {
    "a", "ao", "aos", "aquela", "aquelas", "aquele", "aqueles", "aquilo", "as", "até",
    "com", "como", "da", "das", "de", "dela", "delas", "dele", "deles", "depois", "do",
    "dos", "e", "ela", "elas", "ele", "eles", "em", "entre", "era", "eram", "essa",
    "essas", "esse", "esses", "esta", "estas", "este", "estes", "eu", "foi", "foram",
    "fosse", "fossem", "fui", "gente", "há", "isso", "isto", "já", "la", "lhe", "lhes",
    "lo", "mais", "mas", "me", "mesmo", "meu", "meus", "minha", "minhas", "muito",
    "muita", "muitos", "muitas", "na", "nas", "nem", "nessa", "nesse", "nesta", "neste",
    "no", "nos", "nossa", "nossas", "nosso", "nossos", "num", "numa", "não", "o", "os",
    "ou", "para", "pela", "pelas", "pelo", "pelos", "por", "pra", "pro", "que", "quem",
    "se", "sem", "ser", "seu", "seus", "só", "sua", "suas", "também", "te", "tem",
    "tinha", "tudo", "tu", "um", "uma", "umas", "uns", "você", "vocês", "vou", "aí",
    "ali", "assim", "então", "aqui", "onde", "qual", "quais", "quando", "porque", "pois",
    "ainda", "todo", "toda", "todos", "todas", "ta", "tá", "né", "pq", "vc", "vcs",
    "isso", "esse", "essa", "deve", "devia", "vai", "vão", "vamos", "vez", "sobre",
    "outro", "outra", "outros", "outras", "cada", "qualquer", "sendo", "estão", "vou",
    "agora", "fazer", "está", "pode", "podem", "coisa", "coisas", "sempre", "nada",
    "alguém", "ninguém", "talvez", "antes", "dia", "dias", "hoje", "aqui", "lá",
}

PADRAO_PALAVRA = re.compile(r"[a-zA-ZÀ-ÖØ-öø-ÿ]+")


def _normalizar_plural(palavra: str) -> str:
    """Normalizacao leve de plural (heuristica, nao e um lematizador completo)."""
    if palavra.endswith("ões") and len(palavra) > 5:
        return palavra[:-3] + "ão"
    if palavra.endswith("ais") and len(palavra) > 5:
        return palavra[:-3] + "al"
    if (
        palavra.endswith("s")
        and len(palavra) > 4
        and not palavra.endswith("ês")
        and not palavra.endswith("ns")
    ):
        return palavra[:-1]
    return palavra


def extrair_temas(textos: pd.Series, top_n: int = 10, min_letras: int = 4) -> pd.DataFrame:
    """
    Extrai um ranking simples dos temas (palavras) mais citados em uma serie de
    comentarios, removendo palavras muito curtas e palavras de baixo valor
    semantico (stopwords) e juntando variacoes simples de plural/singular.
    E uma alternativa mais objetiva que uma WordCloud.
    """
    contador = Counter()
    for texto in textos.dropna().astype(str):
        for palavra in PADRAO_PALAVRA.findall(texto.lower()):
            if len(palavra) >= min_letras and palavra not in STOPWORDS_PT:
                contador[_normalizar_plural(palavra)] += 1

    mais_citados = contador.most_common(top_n)
    return pd.DataFrame(mais_citados, columns=["tema", "frequencia"])


# ------------------------------------------------------------------
# RESUMO EXECUTIVO (texto gerado por regras a partir das metricas)
# ------------------------------------------------------------------
def gerar_resumo_executivo(stats: dict) -> str:
    """
    Monta um resumo textual automatico do debate a partir de metricas ja
    calculadas no dashboard. O texto e gerado por regras (sem chamadas a
    internet ou a modelos de linguagem), entao funciona sempre, offline.
    """
    pct_positivo = stats.get("pct_positivo", 0)
    pct_neutro = stats.get("pct_neutro", 0)
    pct_negativo = stats.get("pct_negativo", 0)
    temas_positivos = stats.get("temas_positivos", [])
    temas_negativos = stats.get("temas_negativos", [])
    total_comentarios = stats.get("total_comentarios", 0)
    total_participantes = stats.get("total_participantes", 0)
    tendencia = stats.get("tendencia")  # "melhorou", "piorou", "estavel" ou None

    if total_comentarios == 0:
        return (
            "Ainda não há comentários suficientes no período selecionado para gerar "
            "um resumo do debate."
        )

    frases = []

    # 1) Tom predominante
    maior = max(pct_positivo, pct_neutro, pct_negativo)
    if maior == pct_neutro:
        frases.append(
            f"A maior parte das manifestações apresenta tom neutro ({pct_neutro:.0f}%), "
            "indicando predominância de comentários informativos sobre a proposta em debate."
        )
    elif maior == pct_positivo:
        frases.append(
            f"A maior parte das manifestações apresenta tom favorável ({pct_positivo:.0f}%), "
            "indicando boa aceitação da proposta entre os participantes."
        )
    else:
        frases.append(
            f"A maior parte das manifestações apresenta tom desfavorável ({pct_negativo:.0f}%), "
            "indicando resistência relevante da comunidade em relação à proposta."
        )

    # 2) Temas favoraveis
    if temas_positivos:
        frases.append(
            "Entre as opiniões favoráveis, destacam-se argumentos relacionados a "
            + ", ".join(temas_positivos[:3]) + "."
        )

    # 3) Temas criticos
    if temas_negativos:
        frases.append(
            "Já as manifestações desfavoráveis concentram preocupações com "
            + ", ".join(temas_negativos[:3]) + "."
        )

    # 4) Tendencia ao longo do tempo
    if tendencia == "melhorou":
        frases.append("Nas últimas semanas, o tom geral do debate vem melhorando.")
    elif tendencia == "piorou":
        frases.append("Nas últimas semanas, o tom geral do debate vem piorando.")

    # 5) Volume de participacao
    frases.append(
        f"Ao todo, {formatar_numero(total_participantes)} participantes geraram "
        f"{formatar_numero(total_comentarios)} comentários sobre a proposta no período analisado."
    )

    return " ".join(frases)
