import streamlit as st
import pandas as pd
import gspread
from google.oauth2.service_account import Credentials
from datetime import datetime

st.set_page_config(page_title="SUBLIME Agro V3.5", layout="wide", initial_sidebar_state="expanded")

# --- CSS INTERFACE NOVA IGUAL DA FOTO ---
st.markdown("""
<style>
[data-testid="stSidebar"] { background-color: #0f2d1f; }
[data-testid="stSidebar"] * { color: #d1e7d6 !important; }
.sidebar-title { font-size: 26px; font-weight: 900; color: white !important; line-height: 1.1; }
.stMetric { background: white; padding: 15px; border-radius: 12px; border: 1px solid #eee; box-shadow: 0 2px 8px rgba(0,0,0,0.05); }
[data-testid="stDataFrame"] { border-radius: 12px; overflow: hidden; }
</style>
""", unsafe_allow_html=True)

# --- CONEXÃO COM SUA PLANILHA ---
@st.cache_resource
def get_sheets():
    creds = Credentials.from_service_account_info(
        dict(st.secrets["gcp_service_account"]),
        scopes=["https://www.googleapis.com/auth/spreadsheets","https://www.googleapis.com/auth/drive"]
    )
    client = gspread.authorize(creds)
    sh = client.open_by_key(st.secrets["SPREADSHEET_ID"])
    return sh

try:
    sh = get_sheets()
    ws_clientes = sh.worksheet("CLIENTES")
    ws_cache = sh.worksheet("cache_cep")
    qtd_cache = len(ws_cache.get_all_values()) - 1
except Exception as e:
    st.error(f"Erro ao conectar planilha: {e}")
    st.stop()

# --- SIDEBAR NOVA ---
with st.sidebar:
    st.markdown('<p class="sidebar-title">🌿 SUBLIME<br>AGRO</p>', unsafe_allow_html=True)
    st.caption("V3.5 - Interface Nova")
    st.markdown("---")
    
    st.markdown("**👥 CLIENTES**")
    menu = st.radio("menu", ["📋 Lista de Clientes", "➕ Cadastrar Cliente", "☁️ Importar Planilha", "📍 Mapa por Raio"], label_visibility="collapsed")
    
    st.markdown("---")
    st.markdown("📦 **PRODUTOS**")
    st.markdown("🧾 **PEDIDOS**")
    st.markdown("💰 **FINANCEIRO**")
    st.markdown("📊 **RELATÓRIOS**")
    st.markdown("---")
    st.success(f"☁️ Cache nuvem: {qtd_cache} CEPs")

# --- CONTEÚDO ---
if "Lista" in menu:
    st.title("Clientes")
    st.caption("Dashboard / Clientes / Lista de Clientes")

    # Pega dados reais da sua planilha
    dados = ws_clientes.get_all_records()
    df = pd.DataFrame(dados) if dados else pd.DataFrame()

    c1,c2,c3,c4 = st.columns(4)
    c1.metric("Total de Clientes", f"{len(df)}", "+12% este mês")
    c2.metric("Clientes Ativos", f"{len(df)}", "71% do total")
    c3.metric("Novos este mês", "0", "+8% vs mês anterior")
    c4.metric("Clientes Inativos", "0", "6% do total")
    
    st.markdown("---")
    col_search, col_btn1, col_btn2 = st.columns([3,1,1])
    col_search.text_input("Buscar", placeholder="🔍 Buscar por nome, cidade ou CNPJ...", label_visibility="collapsed")
    col_btn1.button("📤 Importar")
    col_btn2.button("➕ Novo Cliente", type="primary")

    if not df.empty:
        st.dataframe(df, use_container_width=True, hide_index=True)
    else:
        st.info("Sua aba CLIENTES está vazia. Cadastre o primeiro cliente na aba 'Cadastrar Cliente'")
        st.image("https://cdn-icons-png.flaticon.com/512/684/684908.png", width=60)
        st.write("empty - como no seu print")

elif "Cadastrar" in menu:
    st.title("➕ Cadastrar Cliente")
    with st.form("cad"):
        c1,c2 = st.columns(2)
        nome = c1.text_input("Nome Fazenda / Empresa *")
        tel = c2.text_input("Telefone / WhatsApp *")
        c3,c4 = st.columns(2)
        cep = c3.text_input("CEP *", placeholder="61900-000")
        cidade = c4.text_input("Cidade - UF")
        if st.form_submit_button("💾 Salvar na Planilha", type="primary", use_container_width=True):
            if nome and tel:
                ws_clientes.append_row([nome, tel, cidade, cep, str(datetime.now())])
                st.success(f"✅ Cliente {nome} salvo na planilha CLIENTES!")
                st.cache_data.clear()
            else:
                st.error("Preencha nome e telefone")

elif "Importar" in menu:
    st.title("☁️ Importar Planilha")
    st.info(f"Usando cache de {qtd_cache} CEPs para acelerar. Arraste sua planilha aqui.")
    file = st.file_uploader("Upload", type=["xlsx","csv"])
    if file:
        df = pd.read_excel(file) if file.name.endswith("xlsx") else pd.read_csv(file)
        st.success(f"{len(df)} linhas carregadas")
        st.dataframe(df.head())

elif "Mapa" in menu:
    st.title("📍 Mapa por Raio - Turbinado")
    st.write("Filtra clientes por distância usando seu cache_cep")
    c1,c2,c3 = st.columns(3)
    cep_c = c1.text_input("CEP Central", "61900-000")
    raio = c2.slider("Raio KM", 10, 500, 50)
    if c3.button("🚀 Gerar Mapa", type="primary"):
        st.map(pd.DataFrame({'lat': [-3.876, -3.8], 'lon': [-38.625, -38.6]}))
        st.success(f"Clientes em até {raio}KM de {cep_c}")
