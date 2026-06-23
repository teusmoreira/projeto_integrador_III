# 🗳️ Insights da Proposta — Guia Completo

Este guia mostra, **passo a passo e de forma simples**, como instalar o Python, o Streamlit
e abrir o painel no seu computador. Não é preciso ter experiência com programação.

---

## 1. O que é este painel?

É uma página interativa, feita em **Python + Streamlit**, inspirada na tela de **Insights**
de uma plataforma de participação cidadã (estilo Opinate) quando uma proposta está em
debate. Em vez de abas separadas, o conteúdo é organizado em **6 blocos**, em rolagem
única — do panorama geral até um resumo executivo automático:

| Bloco | O que mostra |
| --- | --- |
| 🏛️ **1. Panorama do Debate** | KPIs gerais: participantes, comentários, apoios, votos e tempo em discussão |
| 😊 **2. Sentimento da Comunidade** | Distribuição de sentimentos, evolução no tempo, por região e por faixa etária |
| 👥 **3. Perfil da Participação** | Quem participa (idade, gênero, estado, escolaridade) e como cada grupo percebe a proposta |
| 💬 **4. Principais Temas do Debate** | Ranking dos assuntos mais citados nos comentários, e quais são elogios x críticas |
| ⭐ **5. Comentários em Destaque** | Comentários mais curtidos e mais respondidos, além de uma tabela para explorar/baixar tudo |
| 📝 **6. Resumo Executivo** | Texto gerado automaticamente (por regras, sem internet) resumindo o estado do debate |

Na lateral esquerda há **links de navegação** para pular direto a cada bloco, além dos
**filtros** (sentimento, período, região e faixa etária).

> ⚠️ **Sobre os dados de perfil:** a base de dados original não possui idade, gênero,
> escolaridade nem o estado/município de cada participante — apenas a lista de regiões,
> estados e municípios do Brasil, sem ligação com os usuários. Para que o **Bloco 3**
> pudesse existir, esses campos foram **simulados de forma determinística** (sempre os
> mesmos valores a cada execução) e aparecem marcados com o selo **🧪 perfil simulado**
> na própria tela. Eles servem para demonstrar a funcionalidade, não representam dados
> reais dos participantes.

---

## 2. Estrutura da pasta `Dashboard`

Guarde todos estes arquivos juntos, dentro da pasta chamada **`Dashboard`**:

```
Dashboard/
├── dashboard.py          ← arquivo principal da página de Insights
├── utils.py              ← funções que carregam, tratam e simulam os dados
├── requirements.txt      ← lista de bibliotecas necessárias
├── COMO_USAR.md          ← este guia
├── .streamlit/
│   └── config.toml       ← tema visual (cores) do painel
└── dados/                ← pasta com todos os arquivos .csv
    ├── comment.csv
    ├── comment_sentimento.csv
    ├── comment_vote.csv
    ├── municipality.csv
    ├── proposal_share.csv
    ├── proposal_support.csv
    ├── proposal_vote.csv
    ├── region.csv
    └── state.csv
```

> **Importante:** a pasta `dados` precisa ficar **dentro** da pasta `Dashboard`.
> Se mover os CSVs para outro lugar, o dashboard não vai encontrá-los.

---

## 3. Passo a passo da instalação

### Passo 3.1 — Instalar o Python

1. Acesse **https://www.python.org/downloads/** e baixe o Python (versão 3.10 ou mais nova).
2. Execute o instalador.
3. **MUITO IMPORTANTE (apenas no Windows):** na primeira tela do instalador, marque a
   caixinha **“Add Python to PATH”** antes de clicar em *Install Now*.

Para conferir se deu certo, abra o terminal e digite:

```bash
python --version
```

Deve aparecer algo como `Python 3.12.x`.

> 💡 **Como abrir o terminal:**
> - **Windows:** menu Iniciar → digite `cmd` → abra o *Prompt de Comando*.
> - **macOS:** abra o aplicativo *Terminal*.
> - **Linux:** atalho `Ctrl + Alt + T`.

---

### Passo 3.2 — Entrar na pasta do dashboard

No terminal, vá até a pasta `Dashboard`. Exemplos (ajuste o caminho ao seu computador):

**Windows:**
```bash
cd C:\Users\SeuNome\Desktop\Dashboard
```

**macOS / Linux:**
```bash
cd ~/Desktop/Dashboard
```

> 💡 **Dica fácil:** digite `cd ` (com um espaço depois) e **arraste a pasta `Dashboard`**
> para dentro da janela do terminal. O caminho é preenchido sozinho. Depois pressione Enter.

---

### Passo 3.3 — Instalar o Streamlit e as bibliotecas

Ainda dentro da pasta `Dashboard`, rode o comando abaixo. Ele instala tudo de uma vez
usando o arquivo `requirements.txt`:

```bash
pip install -r requirements.txt
```

Se o comando `pip` não funcionar, tente:

```bash
python -m pip install -r requirements.txt
```

Aguarde a instalação terminar (pode levar alguns minutos na primeira vez).

---

### Passo 3.4 — Abrir o dashboard 🚀

Ainda na pasta `Dashboard`, execute:

```bash
streamlit run dashboard.py
```

Pronto! O dashboard abre **automaticamente no seu navegador**, no endereço:

```
http://localhost:8501
```

Se não abrir sozinho, copie esse endereço e cole na barra do navegador.

---

## 4. Como parar o dashboard

Volte para a janela do terminal e pressione as teclas **`Ctrl + C`**.
Isso encerra o servidor. Para abrir de novo, basta repetir o **Passo 3.4**.

---

## 5. Perguntas frequentes (solução de problemas)

| Problema | Solução |
| --- | --- |
| `'python' não é reconhecido...` (Windows) | O Python não está no PATH. Reinstale marcando **“Add Python to PATH”**, ou use `py` no lugar de `python`. |
| `'streamlit' não é reconhecido...` | A instalação não terminou. Refaça o **Passo 3.3** e tente `python -m streamlit run dashboard.py`. |
| `FileNotFoundError` / não acha os CSVs | Confirme que a pasta `dados` está **dentro** de `Dashboard` e que você rodou o comando **de dentro** da pasta `Dashboard`. |
| A página abre em branco | Atualize o navegador (F5) e aguarde alguns segundos no primeiro carregamento. |
| `pip` não funciona | Use `python -m pip install -r requirements.txt`. |

---

## 6. Resumo rápido (cola para o dia da apresentação)

```bash
# 1) Entrar na pasta
cd caminho/ate/Dashboard

# 2) Instalar (só na primeira vez)
pip install -r requirements.txt

# 3) Abrir o dashboard
streamlit run dashboard.py
```

Bom trabalho e boa apresentação! 🎓
