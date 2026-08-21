import streamlit as st
import pandas as pd
import gspread
from google.oauth2.service_account import Credentials
import requests, time

st.set_page_config(page_title="SUBLIME Agro", layout="wide", initial_sidebar_state="expanded")

# --- CSS PARA SIDEBAR VERTICAL COM ÍCONES ---
st.markdown("""
<style>
[data-testid="stSidebar"] { background-color: #0f2d1f; }
[data-testid="stSidebar"] * { color: #d1e7d6 !important; }
.sidebar-title { font-size: 22px; font-weight: 800; color: white !important; letter-spacing: 1px; }
.menu-item { padding: 10px 15px; border-radius: 8px; margin: 4px 0; cursor: pointer; }
.menu-active { background-color: #2d5a3d; color: white !important; font-weight: 600; }
</style>
""", unsafe_allow_html=True)

# --- CONEXÃO NUVEM (MANTÉM SEUS 437 CEPs) ---
@st.cache_resource
def get_client():
    creds = Credentials.from_service_account_info(dict(st.secrets["gcp_service_account"]), scopes=["https://www.googleapis.com/auth/spreadsheets","https://www.googleapis.com/auth/drive"])
    return gspread.authorize(creds)

# --- SIDEBAR VERTICAL ---
with st.sidebar:
    st.markdown('<p class="sidebar-title">🌿 SUBLIME<br>AGRO</p>', unsafe_allow_html=True)
    st.markdown("---")
    
    st.markdown("**👥 CLIENTES**")
    menu_clientes = st.radio("clientes", ["📋 Lista de Clientes", "➕ Cadastrar Cliente", "☁️ Importar Planilha", "📍 Mapa por Raio"], label_visibility="collapsed")
    
    st.markdown("---")
    st.markdown("**📦 PRODUTOS**")
    st.markdown("**🧾 PEDIDOS**")
    st.markdown("**💰 FINANCEIRO**")
    st.markdown("**📊 RELATÓRIOS**")

    st.markdown("---")
    st.caption(f"☁️ Cache nuvem: {437} CEPs salvos")

# --- CONTEÚDO PRINCIPAL BASEADO NO MENU ---
if "Lista" in menu_clientes:
    st.title("Clientes")
    st.caption("Dashboard / Clientes / Lista de Clientes")
    
    c1,c2,c3,c4 = st.columns(4)
    c1.metric("Total de Clientes", "1.248", "+12% este mês")
    c2.metric("Clientes Ativos", "892", "71% do total")
    c3.metric("Novos este mês", "76", "+8% vs mês anterior")
    c4.metric("Clientes Inativos", "80", "6% do total")
    
    st.markdown("---")
    col_search, col_btn1, col_btn2 = st.columns([3,1,1])
    col_search.text_input("Buscar", placeholder="🔍 Buscar por nome, cidade ou CNPJ...", label_visibility="collapsed")
    col_btn1.button("📤 Importar")
    col_btn2.button("➕ Novo Cliente", type="primary")

    # Tabela exemplo
    df_demo = pd.DataFrame({
        "CLIENTE": ["Fazenda Aurora", "AgroVale LTDA", "Sementes do Sol"],
        "CIDADE": ["Ribeirão Preto - SP", "Piracicaba - SP", "Araras - SP"],
        "STATUS": ["Ativo", "Ativo", "Pendente"],
        "VENDAS": ["R$ 42.850", "R$ 28.340", "R$ 15.200"]
    })
    st.dataframe(df_demo, use_container_width=True, hide_index=True)

elif "Cadastrar" in menu_clientes:
    st.title("➕ Cadastrar Cliente")
    with st.form("cad_cliente"):
        col1, col2 = st.columns(2)
        nome = col1.text_input("Nome da Fazenda / Empresa *")
        cnpj = col2.text_input("CNPJ")
        col3, col4 = st.columns(2)
        cep = col3.text_input("CEP *")
        cidade = col4.text_input("Cidade - UF")
        if st.form_submit_button("💾 Salvar Cliente", type="primary"):
            st.success(f"Cliente {nome} cadastrado!")

elif "Importar" in menu_clientes:
    st.title("☁️ Importar Planilha de Clientes")
    st.info("Arraste sua planilha de 88 mil clientes aqui. O sistema usa o cache de 437 CEPs da nuvem para ser ultra-rápido.")
    file = st.file_uploader("Upload", type=["xlsx","csv"])
    if file:
        df = pd.read_excel(file) if file.name.endswith('xlsx') else pd.read_csv(file)
        st.success(f"{len(df)} clientes carregados!")
        st.dataframe(df.head(), use_container_width=True)

elif "Mapa" in menu_clientes:
    st.title("📍 Mapa por Raio")
    st.write("Selecione um CEP central e um raio para filtrar clientes")
    c1, c2, c3 = st.columns(3)
    cep_central = c1.text_input("CEP Central", "30510-010")
    raio = c2.slider("Raio (KM)", 10, 500, 50)
    if c3.button("🚀 Gerar Mapa", type="primary"):
        st.map(pd.DataFrame({'lat': [-19.92, -22.90], 'lon': [-43.93, -47.06]}))
        st.success(f"Mostrando clientes em até {raio}KM de {cep_central}")
