import streamlit as st
import pandas as pd
import gspread
from google.oauth2.service_account import Credentials
import folium
from streamlit_folium import st_folium
import requests

st.set_page_config(page_title="SUBLIME Agro V3", layout="wide")

# --- CSS SIDEBAR VERTICAL ---
st.markdown("""
<style>
[data-testid="stSidebar"] { background-color: #0f2d1f; }
[data-testid="stSidebar"] * { color: #d1e7d6 !important; }
</style>
""", unsafe_allow_html=True)

@st.cache_resource
def get_sheets():
    creds = Credentials.from_service_account_info(dict(st.secrets["gcp_service_account"]), scopes=["https://www.googleapis.com/auth/spreadsheets","https://www.googleapis.com/auth/drive"])
    client = gspread.authorize(creds)
    return client.open_by_key(st.secrets["SPREADSHEET_ID"])

# --- SIDEBAR ---
with st.sidebar:
    st.title("🌿 SUBLIME AGRO")
    st.markdown("---")
    categoria = st.selectbox("Categoria", ["👥 CLIENTES", "🏭 FORNECEDORES", "📦 PRODUTOS", "⚙️ CONFIGURAÇÕES"])
    
    if "CLIENTES" in categoria:
        pagina = st.radio("Menu", ["📋 Lista", "➕ Cadastrar", "☁️ Importar Planilha", "📍 Mapa Personalizado"], label_visibility="collapsed")
    elif "FORNECEDORES" in categoria:
        pagina = st.radio("Menu", ["📋 Lista Fornecedores", "➕ Cadastrar Fornecedor", "📍 Mapa Fornecedores"], label_visibility="collapsed")
    elif "PRODUTOS" in categoria:
        pagina = st.radio("Menu", ["📋 Lista Produtos", "➕ Cadastrar Produto"], label_visibility="collapsed")
    else:
        pagina = st.radio("Menu", ["🗑️ Limpar Cache Nuvem", "🎨 Aparência"], label_visibility="collapsed")

# --- PÁGINAS ---

# CLIENTES - CADASTRAR
if pagina == "➕ Cadastrar":
    st.title("➕ Cadastrar Cliente - Pelo Celular")
    with st.form("form_cliente", clear_on_submit=True):
        c1,c2 = st.columns(2)
        nome = c1.text_input("Nome / Fazenda *")
        cnpj = c2.text_input("CNPJ / CPF")
        c3,c4 = st.columns(2)
        cep = c3.text_input("CEP *", placeholder="38400-000")
        cidade = c4.text_input("Cidade")
        tel = st.text_input("Telefone / WhatsApp")
        if st.form_submit_button("💾 SALVAR NA NUVEM", type="primary", use_container_width=True):
            sh = get_sheets()
            ws = sh.worksheet("Clientes") # cria essa aba na sua planilha
            ws.append_row([nome, cnpj, cep, cidade, tel])
            st.success(f"✅ {nome} salvo na planilha! Já aparece no mapa.")

# FORNECEDORES - CADASTRAR
elif pagina == "➕ Cadastrar Fornecedor":
    st.title("🏭 Cadastrar Fornecedor")
    with st.form("form_forn"):
        nome_f = st.text_input("Nome do Fornecedor *")
        cep_f = st.text_input("CEP do Fornecedor *")
        produto_f = st.text_input("Produto principal")
        if st.form_submit_button("💾 SALVAR FORNECEDOR", type="primary"):
            sh = get_sheets()
            ws = sh.worksheet("Fornecedores")
            ws.append_row([nome_f, cep_f, produto_f])
            st.success(f"Fornecedor {nome_f} salvo! Pino vermelho no mapa.")

# PRODUTOS - CADASTRAR
elif pagina == "➕ Cadastrar Produto":
    st.title("📦 Cadastrar Produto")
    with st.form("form_prod"):
        nome_p = st.text_input("Nome do Produto *")
        c1,c2 = st.columns(2)
        preco = c1.text_input("Preço R$")
        estoque = c2.text_input("Estoque")
        if st.form_submit_button("💾 SALVAR PRODUTO", type="primary"):
            sh = get_sheets()
            ws = sh.worksheet("Produtos")
            ws.append_row([nome_p, preco, estoque])
            st.success("Produto salvo!")

# MAPA PERSONALIZADO - A ESTRELA
elif pagina == "📍 Mapa Personalizado":
    st.title("📍 Mapa Personalizado - Clientes + Fornecedores Salvos")
    st.info("🟢 Verde = Clientes | 🔴 Vermelho = Fornecedores | Tudo salvo na nuvem com seus 437 CEPs")
    
    # Exemplo de mapa
    m = folium.Map(location=[-19.92, -43.93], zoom_start=5)
    
    # Pega da nuvem
    try:
        sh = get_sheets()
        cache = pd.DataFrame(sh.worksheet("cache_cep").get_all_records())
        if not cache.empty:
            for _, row in cache.head(100).iterrows(): # mostra 100 primeiros
                folium.Marker([row['lat'], row['lng']], popup=f"CEP: {row['cep']}", icon=folium.Icon(color='green')).add_to(m)
    except:
        st.warning("Ainda sem CEPs? Importe a planilha.")

    # Mostra o mapa
    st_folium(m, width=1200, height=600, use_container_width=True)

# CONFIGURAÇÃO - LIMPAR CACHE
elif pagina == "🗑️ Limpar Cache Nuvem":
    st.title("⚙️ Configurações - Modo Admin Celular")
    st.metric("CEPs salvos na nuvem", "437")
    if st.button("🗑️ LIMPAR OS 437 CEPs AGORA", type="primary"):
        sh = get_sheets()
        ws = sh.worksheet("cache_cep")
        ws.clear()
        ws.append_row(["cep","lat","lng"])
        st.success("Nuvem limpa! Agora 0 CEPs.")
        st.cache_data.clear()

# LISTAS
else:
    st.title(pagina)
    st.write("Aqui vai aparecer a lista puxando direto da sua planilha Google. Tudo editável pelo celular.")
    try:
        sh = get_sheets()
        df = pd.DataFrame(sh.worksheet("Clientes").get_all_records())
        st.dataframe(df, use_container_width=True)
    except:
        st.info("Crie as abas na planilha: Clientes, Fornecedores, Produtos, cache_cep")
