import streamlit as st
import pandas as pd
import gspread
from google.oauth2.service_account import Credentials
import folium
from streamlit_folium import st_folium
import time

st.set_page_config(page_title="SUBLIME Agro V3", layout="wide", initial_sidebar_state="expanded")

# --- CSS COM FONTE BRANCA NA SIDEBAR ---
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;600;700;800&display=swap');
* { font-family: 'Inter', sans-serif; }
[data-testid="stHeader"] { display:none; }
[data-testid="stAppViewContainer"] { background-color: #f5f5f0; }
[data-testid="stSidebar"] { background-color: #122e1c !important; }
[data-testid="stSidebar"] * { color: #e8f5e9 !important; }
[data-testid="stSidebar"] [data-testid="stExpander"] summary { background-color: #2e5a3d !important; border-radius: 8px; }
[data-testid="stSidebar"] [data-testid="stExpander"] summary p { color: #ffffff !important; font-weight: 800 !important; }
[data-testid="stSidebar"] [data-testid="stRadio"] label p { color: #dcedc8 !important; }
[data-testid="stSidebar"] [data-testid="stRadio"] label[data-checked="true"] p { color: #ffffff !important; font-weight: 700 !important; }
.card { background: white; border-radius: 16px; padding: 20px; box-shadow: 0 2px 12px rgba(0,0,0,0.06); }
</style>
""", unsafe_allow_html=True)

@st.cache_resource
def get_client():
    creds = Credentials.from_service_account_info(
        dict(st.secrets["gcp_service_account"]),
        scopes=["https://www.googleapis.com/auth/spreadsheets","https://www.googleapis.com/auth/drive"]
    )
    return gspread.authorize(creds)

# --- FUNÇÃO COM CACHE DE 5 MINUTOS - RESOLVE O ERRO 429 ---
@st.cache_data(ttl=300, show_spinner=False)
def load_dados_planilha():
    try:
        client = get_client()
        sh = client.open_by_key(st.secrets["SPREADSHEET_ID"])
        ws_c = sh.worksheet("Clientes")
        ws_f = sh.worksheet("Fornecedores")
        ws_p = sh.worksheet("Produtos")
        ws_cache = sh.worksheet("cache_cep")
        
        # Lê tudo de uma vez, sem ficar chamando várias vezes
        dados_c = ws_c.get_all_records()
        dados_f = ws_f.get_all_records()
        qtd_cache = len(ws_cache.col_values(1)) - 1
        
        return pd.DataFrame(dados_c), pd.DataFrame(dados_f), qtd_cache, None
    except Exception as e:
        # Se der 429, retorna o erro pra mostrar mensagem amigável
        if "429" in str(e) or "Quota" in str(e):
            return pd.DataFrame(), pd.DataFrame(), 0, "QUOTA"
        return pd.DataFrame(), pd.DataFrame(), 0, str(e)

# Tenta carregar com retry
df_clientes, df_forn, qtd_cache, erro = load_dados_planilha()

if erro == "QUOTA":
    st.warning("⏳ O Google Sheets atingiu o limite de leituras (60 por minuto).")
    st.info("Aguarde 60 segundos e clique no botão abaixo. O novo código com cache de 5 minutos já vai evitar isso.")
    if st.button("🔄 Tentar novamente (após 60s)", type="primary"):
        st.cache_data.clear()
        st.rerun()
    st.stop()
elif erro:
    st.error(f"Erro ao conectar: {erro}")
    st.stop()

# --- TOPO E SIDEBAR IGUAL ANTES ---
c1,c2,c3 = st.columns([2,3,2])
with c1:
    st.markdown('<div style="font-size:26px; font-weight:900; color:#1a2a4a;">🌱 SUBLIME <span style="background:#c5e1a5; color:#2e7d32; font-size:13px; padding:2px 8px; border-radius:6px;">V3</span><div style="font-size:18px; margin-top:-5px;">Agro</div></div>', unsafe_allow_html=True)
with c2:
    st.text_input("busca", placeholder="🔍 Buscar clientes, fornecedores, produtos...", label_visibility="collapsed")
with c3:
    st.markdown('<div style="text-align:right">🔔 ❓ <b>Ana Silva</b> ⌄ ⚙️</div>', unsafe_allow_html=True)

with st.sidebar:
    st.markdown('<div style="padding:20px 10px;"><div style="font-size:26px; font-weight:900; color:white;">🌿 SUBLIME<br>AGRO</div></div>', unsafe_allow_html=True)
    with st.expander("👥 CLIENTES", expanded=True):
        menu = st.radio("menu_cli", ["• Lista", "• Cadastrar Cliente", "• Importar Planilha", "• Mapa Personalizado"], label_visibility="collapsed")
    with st.expander("🚚 FORNECEDORES", expanded=False):
        st.write("• Lista")
    with st.expander("📦 PRODUTOS", expanded=False):
        st.write("• Lista")
    st.markdown(f'<div style="background:#2e7d32; color:white; padding:6px 12px; border-radius:20px; font-size:11px; margin:10px; text-align:center;">☁️ {qtd_cache} CEPs em cache | Cache 5min ativo</div>', unsafe_allow_html=True)

# --- CONTEÚDO ---
st.markdown(f'<h1 style="color:#1a2a4a;">Gestão de Clientes & Fornecedores</h1><p style="color:gray;">{len(df_clientes)} clientes • {len(df_forn)} fornecedores • {qtd_cache} CEPs</p>', unsafe_allow_html=True)

col_mapa, col_form = st.columns([1.7, 1])
with col_mapa:
    st.markdown('<div class="card"><h3>Mapa de Clientes e Fornecedores</h3>', unsafe_allow_html=True)
    m = folium.Map(location=[-23.2, -45.9], zoom_start=10, tiles="CartoDB positron")
    if len(df_clientes)==0:
        for lat, lon in [(-23.15,-45.95), (-23.18,-45.93), (-23.22,-45.88)]:
            folium.Marker([lat, lon], icon=folium.Icon(color='green')).add_to(m)
    st_folium(m, width=700, height=480)
    st.markdown('</div>', unsafe_allow_html=True)

with col_form:
    st.markdown('<div class="card"><h3>+ Cadastrar Cliente</h3>', unsafe_allow_html=True)
    with st.form("form_v3"):
        nome = st.text_input("Nome completo", placeholder="Ex: Fazenda São João Ltda")
        doc = st.text_input("CPF/CNPJ")
        tel = st.text_input("Telefone")
        cidade = st.text_input("Cidade")
        if st.form_submit_button("✓ Salvar Cliente", type="primary", use_container_width=True) and nome:
            try:
                client = get_client()
                sh = client.open_by_key(st.secrets["SPREADSHEET_ID"])
                sh.worksheet("Clientes").append_row([nome, doc, tel, cidade])
                st.cache_data.clear()
                st.success(f"✅ {nome} salvo!")
                st.balloons()
            except Exception as e:
                st.error(f"Erro ao salvar: {e}")
    st.markdown('</div>', unsafe_allow_html=True)
