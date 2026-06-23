"""
============================================================
  INSIGHTS DA PROPOSTA
  Modulo analitico inspirado na tela de Insights da Opinate,
  para acompanhar uma proposta em debate na plataforma.
============================================================
Como executar (no terminal, dentro da pasta Dashboard):

    streamlit run dashboard.py

O navegador abre sozinho em http://localhost:8501
============================================================
"""

import html

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

from utils import (
    carregar_dados,
    extrair_temas,
    formatar_numero,
    formatar_tempo_discussao,
    gerar_resumo_executivo,
)

# ------------------------------------------------------------------
# 1. CONFIGURACAO GERAL DA PAGINA
# ------------------------------------------------------------------
st.set_page_config(
    page_title="Insights da Proposta",
    page_icon="🗳️",
    layout="wide",
    initial_sidebar_state="expanded",
)

# Paleta de cores usada nos graficos (tons sobrios e profissionais)
COR_PRIMARIA = "#2563EB"
COR_POSITIVO = "#16A34A"
COR_NEUTRO = "#94A3B8"
COR_NEGATIVO = "#DC2626"
PALETA_SEQUENCIAL = px.colors.sequential.Blues

CORES_SENTIMENTO = {
    "Positivo": COR_POSITIVO,
    "Neutro": COR_NEUTRO,
    "Negativo": COR_NEGATIVO,
}

# ------------------------------------------------------------------
# 2. ESTILO VISUAL (CSS) - deixa a pagina com cara de produto, nao de BI
# ------------------------------------------------------------------
st.markdown(
    """
    <style>
        @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap');

        html, body, [class*="css"] { font-family: 'Inter', sans-serif; }

        /* Fundo principal */
        .stApp { background-color: #F8FAFC; }

        /* Cartoes de metrica (KPIs) */
        div[data-testid="stMetric"] {
            background-color: #FFFFFF;
            border: 1px solid #E2E8F0;
            border-radius: 14px;
            padding: 18px 20px;
            box-shadow: 0 1px 3px rgba(0,0,0,0.06);
        }
        div[data-testid="stMetric"] label p {
            font-size: 0.85rem;
            color: #64748B;
            font-weight: 600;
        }
        div[data-testid="stMetricValue"] {
            font-size: 1.9rem;
            font-weight: 700;
            color: #1E293B;
        }

        /* Titulo principal */
        .titulo-principal {
            font-size: 2.1rem;
            font-weight: 800;
            color: #1E293B;
            margin-bottom: 0px;
        }
        .subtitulo-principal {
            font-size: 1rem;
            color: #64748B;
            margin-top: 2px;
        }

        /* Numero do bloco (eyebrow) */
        .bloco-eyebrow {
            display: inline-flex;
            align-items: center;
            gap: 8px;
            font-size: 0.8rem;
            font-weight: 700;
            letter-spacing: 0.06em;
            color: #2563EB;
            text-transform: uppercase;
            margin-bottom: 2px;
        }
        .bloco-numero {
            display: inline-flex;
            align-items: center;
            justify-content: center;
            width: 22px;
            height: 22px;
            border-radius: 50%;
            background-color: #2563EB;
            color: #FFFFFF;
            font-size: 0.72rem;
            font-weight: 800;
        }

        /* Cabecalho de secao */
        .secao {
            font-size: 1.45rem;
            font-weight: 700;
            color: #1E293B;
            margin: 2px 0 2px 0;
        }
        .secao-caption {
            color: #64748B;
            font-size: 0.92rem;
            margin-bottom: 14px;
        }

        /* Badge de "dados simulados" */
        .badge-simulado {
            display: inline-block;
            background-color: #FEF3C7;
            color: #92400E;
            border: 1px solid #FDE68A;
            border-radius: 999px;
            padding: 2px 10px;
            font-size: 0.72rem;
            font-weight: 700;
            margin-left: 8px;
            vertical-align: middle;
        }

        /* Card do resumo executivo */
        .resumo-card {
            background-color: #FFFFFF;
            border: 1px solid #E2E8F0;
            border-left: 6px solid #2563EB;
            border-radius: 14px;
            padding: 22px 26px;
            box-shadow: 0 1px 3px rgba(0,0,0,0.06);
            font-size: 1.04rem;
            line-height: 1.7;
            color: #1E293B;
        }
        .resumo-titulo {
            font-size: 0.78rem;
            font-weight: 700;
            letter-spacing: 0.06em;
            text-transform: uppercase;
            color: #2563EB;
            margin-bottom: 8px;
        }

        /* Chips de temas positivos / criticos */
        .tema-chip {
            display: inline-block;
            border-radius: 999px;
            padding: 5px 14px;
            margin: 4px 6px 4px 0;
            font-size: 0.86rem;
            font-weight: 600;
        }
        .tema-chip-positivo { background-color: #DCFCE7; color: #166534; }
        .tema-chip-negativo { background-color: #FEE2E2; color: #991B1B; }

        /* Cards de comentarios em destaque */
        .comment-card {
            background-color: #FFFFFF;
            border: 1px solid #E2E8F0;
            border-radius: 12px;
            padding: 14px 16px;
            margin-bottom: 12px;
            box-shadow: 0 1px 2px rgba(0,0,0,0.04);
        }
        .comment-card-positivo { border-left: 5px solid #16A34A; }
        .comment-card-neutro { border-left: 5px solid #94A3B8; }
        .comment-card-negativo { border-left: 5px solid #DC2626; }
        .comment-card-texto {
            color: #1E293B;
            font-size: 0.94rem;
            line-height: 1.5;
            margin-bottom: 8px;
        }
        .comment-card-meta {
            color: #64748B;
            font-size: 0.8rem;
        }

        /* Esconder o menu padrao e o rodape do Streamlit */
        #MainMenu { visibility: hidden; }
        footer { visibility: hidden; }
    </style>
    """,
    unsafe_allow_html=True,
)


def cabecalho_bloco(numero: str, titulo: str, legenda: str, badge: bool = False):
    """Desenha o cabecalho padrao de cada bloco da pagina de Insights."""
    selo = '<span class="badge-simulado">🧪 perfil simulado</span>' if badge else ""
    st.markdown(
        f"""
        <p class="bloco-eyebrow"><span class="bloco-numero">{numero}</span> BLOCO {numero}</p>
        <p class="secao">{titulo}{selo}</p>
        <p class="secao-caption">{legenda}</p>
        """,
        unsafe_allow_html=True,
    )


# ------------------------------------------------------------------
# 3. CARREGAMENTO DOS DADOS
# ------------------------------------------------------------------
dados = carregar_dados()

comentarios = dados["comentarios"]
sentimentos = dados["sentimentos"]
votos_comentario = dados["votos_comentario"]
votos_proposta = dados["votos_proposta"]
apoios = dados["apoios"]
compartilhamentos = dados["compartilhamentos"]
perfil = dados["perfil"]

# Datas globais (usadas no calculo do "tempo em discussao", que nao muda com filtro)
datas_globais = pd.concat(
    [
        comentarios["created_at"],
        votos_comentario["created_at"],
        votos_proposta["created_at"],
        apoios["created_at"],
        compartilhamentos["created_at"],
    ]
).dropna()
data_inicio_global = datas_globais.min()
data_fim_global = datas_globais.max()

# ------------------------------------------------------------------
# 4. BARRA LATERAL (NAVEGACAO + FILTROS)
# ------------------------------------------------------------------
with st.sidebar:
    st.markdown("## 🗳️ Insights")
    st.caption("Painel analitico da proposta em debate.")

    st.markdown(
        """
        - [🏛️ Panorama do debate](#panorama)
        - [😊 Sentimento da comunidade](#sentimento)
        - [👥 Perfil da participação](#perfil)
        - [💬 Principais temas](#temas)
        - [⭐ Comentários em destaque](#destaque)
        - [📝 Resumo executivo](#resumo)
        """
    )

    st.markdown("---")
    st.markdown("### 🎛️ Filtros")

    opcoes_sentimento = sorted(sentimentos["sentimento"].dropna().unique().tolist())
    sentimento_sel = st.multiselect(
        "Sentimento do comentário",
        options=opcoes_sentimento,
        default=opcoes_sentimento,
    )

    data_min = sentimentos["created_at"].min().date()
    data_max = sentimentos["created_at"].max().date()
    periodo = st.date_input(
        "Período",
        value=(data_min, data_max),
        min_value=data_min,
        max_value=data_max,
    )

    opcoes_regiao = sorted(perfil["regiao"].dropna().unique().tolist())
    regiao_sel = st.multiselect("Região", options=opcoes_regiao, default=opcoes_regiao)

    opcoes_faixa = ["18-25", "26-35", "36-45", "46-60", "60+"]
    faixa_sel = st.multiselect("Faixa etária", options=opcoes_faixa, default=opcoes_faixa)

    st.markdown("---")
    st.caption(
        "🧪 Os campos de idade, gênero, escolaridade e localização são "
        "**simulados** para fins de demonstração — a base original não inclui "
        "esses dados por usuário."
    )
    st.caption("Projeto acadêmico desenvolvido em Python + Streamlit.")

if isinstance(periodo, (list, tuple)) and len(periodo) == 2:
    periodo_inicio, periodo_fim = periodo
else:
    periodo_inicio, periodo_fim = data_min, data_max


def filtrar_periodo(df: pd.DataFrame, coluna: str = "created_at") -> pd.DataFrame:
    """Filtra um DataFrame pelo intervalo de datas escolhido na barra lateral."""
    return df[(df[coluna].dt.date >= periodo_inicio) & (df[coluna].dt.date <= periodo_fim)]


def filtrar_perfil(df: pd.DataFrame) -> pd.DataFrame:
    """Junta o perfil simulado e filtra por região/faixa etária (sem afetar sentimento)."""
    base = df.merge(
        perfil[["user_id", "faixa_etaria", "regiao", "genero", "escolaridade"]],
        on="user_id",
        how="left",
    )
    if regiao_sel:
        base = base[base["regiao"].isin(regiao_sel)]
    if faixa_sel:
        base = base[base["faixa_etaria"].isin(faixa_sel)]
    return base


# Conjuntos filtrados por periodo + perfil (regiao/faixa etaria)
comentarios_f = filtrar_perfil(filtrar_periodo(comentarios))
votos_comentario_f = filtrar_perfil(filtrar_periodo(votos_comentario))
votos_proposta_f = filtrar_perfil(filtrar_periodo(votos_proposta))
apoios_f = filtrar_perfil(filtrar_periodo(apoios))
compartilhamentos_f = filtrar_perfil(filtrar_periodo(compartilhamentos))

# Sentimentos: ja vem com o perfil simulado embutido (gerado em utils.carregar_dados)
sent_filtrado = filtrar_periodo(sentimentos)
if regiao_sel:
    sent_filtrado = sent_filtrado[sent_filtrado["regiao"].isin(regiao_sel)]
if faixa_sel:
    sent_filtrado = sent_filtrado[sent_filtrado["faixa_etaria"].isin(faixa_sel)]
if sentimento_sel:
    sent_filtrado = sent_filtrado[sent_filtrado["sentimento"].isin(sentimento_sel)]

participantes_filtrados = pd.concat(
    [
        comentarios_f["user_id"],
        votos_comentario_f["user_id"],
        votos_proposta_f["user_id"],
        apoios_f["user_id"],
        compartilhamentos_f["user_id"],
    ]
).nunique()

# ------------------------------------------------------------------
# 5. CABECALHO
# ------------------------------------------------------------------
st.markdown('<p class="titulo-principal">🗳️ Insights da Proposta</p>', unsafe_allow_html=True)
st.markdown(
    '<p class="subtitulo-principal">Como a comunidade está reagindo, quem está '
    "participando e quais temas dominam o debate.</p>",
    unsafe_allow_html=True,
)
st.write("")

# ============================================================
# BLOCO 1 — PANORAMA DO DEBATE
# ============================================================
st.header("", anchor="panorama")
cabecalho_bloco(
    "1",
    "Panorama do Debate",
    "Visão geral de quem participou e como a proposta está sendo discutida.",
)

c1, c2, c3, c4, c5 = st.columns(5)
c1.metric("👥 Participantes", formatar_numero(participantes_filtrados))
c2.metric("💬 Comentários", formatar_numero(len(sent_filtrado)))
c3.metric("🤝 Apoios à proposta", formatar_numero(len(apoios_f)))
c4.metric("🗳️ Votos", formatar_numero(len(votos_proposta_f) + len(votos_comentario_f)))
c5.metric("⏳ Tempo em discussão", formatar_tempo_discussao(data_inicio_global, data_fim_global))

st.caption(f"🔁 {formatar_numero(len(compartilhamentos_f))} compartilhamentos no período selecionado.")

st.write("")
st.divider()

# ============================================================
# BLOCO 2 — SENTIMENTO DA COMUNIDADE
# ============================================================
st.header("", anchor="sentimento")
cabecalho_bloco(
    "2",
    "Sentimento da Comunidade",
    "Como a comunidade está reagindo à proposta — tom geral, evolução no tempo, "
    "região e faixa etária.",
)

if sent_filtrado.empty:
    st.info("Não há comentários para os filtros selecionados.")
else:
    c1, c2 = st.columns(2)

    with c1:
        contagem_sent = sent_filtrado["sentimento"].value_counts().reset_index()
        contagem_sent.columns = ["sentimento", "quantidade"]
        fig = px.pie(
            contagem_sent,
            names="sentimento",
            values="quantidade",
            hole=0.55,
            color="sentimento",
            color_discrete_map=CORES_SENTIMENTO,
            title="Distribuição dos sentimentos",
        )
        fig.update_traces(textposition="inside", textinfo="percent+label")
        fig.update_layout(showlegend=True, height=360, margin=dict(t=50, b=10))
        st.plotly_chart(fig, use_container_width=True)

    with c2:
        temp = sent_filtrado.copy()
        temp["mes"] = temp["created_at"].dt.to_period("M").dt.to_timestamp()
        por_mes_sent = temp.groupby(["mes", "sentimento"]).size().reset_index(name="quantidade")
        fig = px.line(
            por_mes_sent,
            x="mes",
            y="quantidade",
            color="sentimento",
            color_discrete_map=CORES_SENTIMENTO,
            markers=True,
            title="Evolução do sentimento ao longo do tempo",
        )
        fig.update_layout(height=360, margin=dict(t=50, b=10), xaxis_title="", yaxis_title="Comentários")
        st.plotly_chart(fig, use_container_width=True)

    c3, c4 = st.columns(2)

    with c3:
        por_regiao = (
            sent_filtrado.groupby(["regiao", "sentimento"]).size().reset_index(name="quantidade")
        )
        total_regiao = por_regiao.groupby("regiao")["quantidade"].transform("sum")
        por_regiao["percentual"] = (por_regiao["quantidade"] / total_regiao) * 100
        fig = px.bar(
            por_regiao,
            x="percentual",
            y="regiao",
            color="sentimento",
            orientation="h",
            color_discrete_map=CORES_SENTIMENTO,
            title="Sentimento por região",
            text_auto=".0f",
        )
        fig.update_layout(
            height=360, margin=dict(t=50, b=10), barmode="stack",
            xaxis_title="% dos comentários", yaxis_title="",
        )
        st.plotly_chart(fig, use_container_width=True)

    with c4:
        por_faixa = (
            sent_filtrado.groupby(["faixa_etaria", "sentimento"], observed=True)
            .size()
            .reset_index(name="quantidade")
        )
        total_faixa = por_faixa.groupby("faixa_etaria", observed=True)["quantidade"].transform("sum")
        por_faixa["percentual"] = (por_faixa["quantidade"] / total_faixa) * 100
        fig = px.bar(
            por_faixa,
            x="faixa_etaria",
            y="percentual",
            color="sentimento",
            color_discrete_map=CORES_SENTIMENTO,
            title="Sentimento por faixa etária",
            text_auto=".0f",
        )
        fig.update_layout(
            height=360, margin=dict(t=50, b=10), barmode="stack",
            xaxis_title="", yaxis_title="% dos comentários",
        )
        st.plotly_chart(fig, use_container_width=True)

st.write("")
st.divider()

# ============================================================
# BLOCO 3 — PERFIL DA PARTICIPAÇÃO
# ============================================================
st.header("", anchor="perfil")
cabecalho_bloco(
    "3",
    "Perfil da Participação",
    "Quem está participando do debate — e como cada grupo percebe a proposta.",
    badge=True,
)

perfil_filtrado = perfil[
    perfil["regiao"].isin(regiao_sel) & perfil["faixa_etaria"].isin(faixa_sel)
]

if perfil_filtrado.empty:
    st.info("Não há participantes para os filtros selecionados.")
else:
    st.markdown("**Quem está participando?**")
    c1, c2, c3, c4 = st.columns(4)

    with c1:
        cont = perfil_filtrado["faixa_etaria"].value_counts().sort_index().reset_index()
        cont.columns = ["faixa_etaria", "quantidade"]
        fig = px.bar(
            cont, x="faixa_etaria", y="quantidade", title="Faixa etária",
            color_discrete_sequence=[COR_PRIMARIA],
        )
        fig.update_layout(height=300, margin=dict(t=40, b=10), xaxis_title="", yaxis_title="")
        st.plotly_chart(fig, use_container_width=True)

    with c2:
        cont = perfil_filtrado["genero"].value_counts().reset_index()
        cont.columns = ["genero", "quantidade"]
        fig = px.pie(
            cont, names="genero", values="quantidade", hole=0.5, title="Gênero",
            color_discrete_sequence=px.colors.sequential.Blues_r,
        )
        fig.update_traces(textposition="inside", textinfo="percent")
        fig.update_layout(height=300, margin=dict(t=40, b=10), showlegend=True,
                           legend=dict(orientation="h", yanchor="bottom", y=-0.4))
        st.plotly_chart(fig, use_container_width=True)

    with c3:
        cont = perfil_filtrado["estado"].value_counts().head(8).reset_index()
        cont.columns = ["estado", "quantidade"]
        fig = px.bar(
            cont.sort_values("quantidade"), x="quantidade", y="estado", orientation="h",
            title="Estado (top 8)", color="quantidade", color_continuous_scale=PALETA_SEQUENCIAL,
        )
        fig.update_layout(height=300, margin=dict(t=40, b=10), coloraxis_showscale=False,
                           xaxis_title="", yaxis_title="")
        st.plotly_chart(fig, use_container_width=True)

    with c4:
        ordem_escolaridade = ["Fundamental", "Médio", "Superior", "Pós-graduação"]
        cont = perfil_filtrado["escolaridade"].value_counts().reindex(ordem_escolaridade).reset_index()
        cont.columns = ["escolaridade", "quantidade"]
        fig = px.bar(
            cont, x="escolaridade", y="quantidade", title="Escolaridade",
            color_discrete_sequence=[COR_PRIMARIA],
        )
        fig.update_layout(height=300, margin=dict(t=40, b=10), xaxis_title="", yaxis_title="")
        st.plotly_chart(fig, use_container_width=True)

    st.write("")
    st.markdown("**Como cada grupo percebe a proposta?**")

    dimensao_label = st.selectbox(
        "Agrupar por", ["Faixa etária", "Gênero", "Escolaridade", "Região"], index=0
    )
    coluna_dimensao = {
        "Faixa etária": "faixa_etaria",
        "Gênero": "genero",
        "Escolaridade": "escolaridade",
        "Região": "regiao",
    }[dimensao_label]

    if sent_filtrado.empty:
        st.info("Não há comentários suficientes para montar o cruzamento.")
    else:
        cruzamento = (
            pd.crosstab(sent_filtrado[coluna_dimensao], sent_filtrado["sentimento"], normalize="index")
            * 100
        )
        for col in ["Positivo", "Neutro", "Negativo"]:
            if col not in cruzamento.columns:
                cruzamento[col] = 0.0
        cruzamento = cruzamento[["Positivo", "Neutro", "Negativo"]].round(0).astype(int)
        cruzamento.columns = ["Positivo (%)", "Neutro (%)", "Negativo (%)"]
        cruzamento.index.name = dimensao_label
        st.dataframe(cruzamento, use_container_width=True)

st.write("")
st.divider()

# ============================================================
# BLOCO 4 — PRINCIPAIS TEMAS DO DEBATE
# ============================================================
st.header("", anchor="temas")
cabecalho_bloco(
    "4",
    "Principais Temas do Debate",
    "Os assuntos mais citados nos comentários, e como eles se dividem entre "
    "elogios e críticas.",
)

if sent_filtrado.empty:
    st.info("Não há comentários para os filtros selecionados.")
else:
    temas_gerais = extrair_temas(sent_filtrado["content"], top_n=10)
    if temas_gerais.empty:
        st.info("Não foi possível identificar temas com os filtros atuais.")
    else:
        fig = px.bar(
            temas_gerais.sort_values("frequencia"),
            x="frequencia", y="tema", orientation="h",
            title="Temas mais citados", color="frequencia",
            color_continuous_scale=PALETA_SEQUENCIAL, text_auto=True,
        )
        fig.update_layout(height=380, margin=dict(t=50, b=10), coloraxis_showscale=False,
                           xaxis_title="Menções", yaxis_title="")
        st.plotly_chart(fig, use_container_width=True)

    c1, c2 = st.columns(2)

    with c1:
        st.markdown("**🟢 Temas positivos**")
        temas_pos = extrair_temas(
            sent_filtrado[sent_filtrado["sentimento"] == "Positivo"]["content"], top_n=8
        )
        if temas_pos.empty:
            st.caption("Sem temas suficientes para este recorte.")
        else:
            chips = "".join(
                f'<span class="tema-chip tema-chip-positivo">{html.escape(t)}</span>'
                for t in temas_pos["tema"]
            )
            st.markdown(chips, unsafe_allow_html=True)

    with c2:
        st.markdown("**🔴 Temas críticos**")
        temas_neg = extrair_temas(
            sent_filtrado[sent_filtrado["sentimento"] == "Negativo"]["content"], top_n=8
        )
        if temas_neg.empty:
            st.caption("Sem temas suficientes para este recorte.")
        else:
            chips = "".join(
                f'<span class="tema-chip tema-chip-negativo">{html.escape(t)}</span>'
                for t in temas_neg["tema"]
            )
            st.markdown(chips, unsafe_allow_html=True)

st.write("")
st.divider()

# ============================================================
# BLOCO 5 — COMENTÁRIOS EM DESTAQUE
# ============================================================
st.header("", anchor="destaque")
cabecalho_bloco(
    "5",
    "Comentários em Destaque",
    "Os comentários com maior repercussão — mais curtidos e mais respondidos.",
)

EMOJI_SENTIMENTO = {"Positivo": "🟢", "Neutro": "⚪", "Negativo": "🔴"}


def desenhar_cards_comentarios(df_top: pd.DataFrame, coluna_metrica: str, rotulo_metrica: str):
    if df_top.empty:
        st.caption("Sem comentários suficientes para este recorte.")
        return
    for _, linha in df_top.iterrows():
        sentimento = linha.get("sentimento", "Neutro")
        classe = {
            "Positivo": "comment-card-positivo",
            "Neutro": "comment-card-neutro",
            "Negativo": "comment-card-negativo",
        }.get(sentimento, "comment-card-neutro")
        texto = html.escape(str(linha["content"]))
        if len(texto) > 280:
            texto = texto[:280] + "…"
        st.markdown(
            f"""
            <div class="comment-card {classe}">
                <div class="comment-card-texto">{texto}</div>
                <div class="comment-card-meta">
                    {EMOJI_SENTIMENTO.get(sentimento, "⚪")} {sentimento} ·
                    👍 {formatar_numero(linha['aux_likes_comentario'])} curtidas ·
                    💬 {formatar_numero(linha['aux_respostas'])} respostas
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )


aba_likes, aba_respostas, aba_explorar = st.tabs(
    ["💙 Mais curtidos", "💬 Mais respondidos", "🔍 Explorar todos"]
)

with aba_likes:
    top_likes = sent_filtrado.sort_values("aux_likes_comentario", ascending=False).head(5)
    desenhar_cards_comentarios(top_likes, "aux_likes_comentario", "curtidas")

with aba_respostas:
    top_respostas = sent_filtrado.sort_values("aux_respostas", ascending=False).head(5)
    desenhar_cards_comentarios(top_respostas, "aux_respostas", "respostas")

with aba_explorar:
    busca = st.text_input("🔍 Buscar palavra no comentário", "")
    tabela = sent_filtrado[
        ["content", "sentimento", "emocao_principal", "aux_likes_comentario", "aux_respostas", "created_at"]
    ].rename(
        columns={
            "content": "Comentário",
            "sentimento": "Sentimento",
            "emocao_principal": "Emoção",
            "aux_likes_comentario": "Curtidas",
            "aux_respostas": "Respostas",
            "created_at": "Data",
        }
    )
    if busca.strip():
        tabela = tabela[tabela["Comentário"].astype(str).str.contains(busca, case=False, na=False)]

    st.write(f"Mostrando **{len(tabela)}** comentários.")
    st.dataframe(tabela, use_container_width=True, hide_index=True, height=420)

    csv = tabela.to_csv(index=False).encode("utf-8-sig")
    st.download_button(
        "⬇️ Baixar comentários filtrados (CSV)",
        data=csv,
        file_name="comentarios_filtrados.csv",
        mime="text/csv",
    )

st.write("")
st.divider()

# ============================================================
# BLOCO 6 — RESUMO EXECUTIVO
# ============================================================
st.header("", anchor="resumo")
cabecalho_bloco(
    "6",
    "Resumo Executivo",
    "Síntese automática dos principais pontos do debate, gerada a partir das métricas acima.",
)

if sent_filtrado.empty:
    pct_positivo = pct_neutro = pct_negativo = 0
    temas_pos_lista, temas_neg_lista = [], []
    tendencia = None
else:
    pct_positivo = (sent_filtrado["sentimento"] == "Positivo").mean() * 100
    pct_neutro = (sent_filtrado["sentimento"] == "Neutro").mean() * 100
    pct_negativo = (sent_filtrado["sentimento"] == "Negativo").mean() * 100

    temas_pos_lista = extrair_temas(
        sent_filtrado[sent_filtrado["sentimento"] == "Positivo"]["content"], top_n=5
    )["tema"].tolist()
    temas_neg_lista = extrair_temas(
        sent_filtrado[sent_filtrado["sentimento"] == "Negativo"]["content"], top_n=5
    )["tema"].tolist()

    mediana_data = sent_filtrado["created_at"].median()
    primeira_metade = sent_filtrado[sent_filtrado["created_at"] <= mediana_data]
    segunda_metade = sent_filtrado[sent_filtrado["created_at"] > mediana_data]
    pct_pos_1 = (primeira_metade["sentimento"] == "Positivo").mean() * 100 if len(primeira_metade) else 0
    pct_pos_2 = (segunda_metade["sentimento"] == "Positivo").mean() * 100 if len(segunda_metade) else 0
    if pct_pos_2 - pct_pos_1 > 5:
        tendencia = "melhorou"
    elif pct_pos_1 - pct_pos_2 > 5:
        tendencia = "piorou"
    else:
        tendencia = "estavel"

stats_resumo = {
    "pct_positivo": pct_positivo,
    "pct_neutro": pct_neutro,
    "pct_negativo": pct_negativo,
    "temas_positivos": temas_pos_lista,
    "temas_negativos": temas_neg_lista,
    "total_comentarios": len(sent_filtrado),
    "total_participantes": participantes_filtrados,
    "tendencia": tendencia,
}
texto_resumo = gerar_resumo_executivo(stats_resumo)

st.markdown(
    f"""
    <div class="resumo-card">
        <div class="resumo-titulo">📝 Resumo do debate</div>
        {html.escape(texto_resumo)}
    </div>
    """,
    unsafe_allow_html=True,
)

# ------------------------------------------------------------------
# 7. RODAPE
# ------------------------------------------------------------------
st.write("")
st.divider()
st.caption(
    "Painel de Insights desenvolvido em Python com Streamlit e Plotly | "
    "Projeto acadêmico — simulação do módulo analítico de uma plataforma de participação cidadã."
)
