import streamlit as st
import pandas as pd
import gspread
from google.oauth2.service_account import Credentials
import folium
from streamlit_folium import st_folium

st.set_page_config(page_title="SUBLIME Agro V3", layout="wide", initial_sidebar_state="expanded")

# --- CSS V3.6.1 - SIDEBAR FONTE CLARA ---
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;600;700;800&display=swap');
* { font-family: 'Inter', sans-serif; }
[data-testid="stHeader"] { display:none; }
[data-testid="stAppViewContainer"] { background-color: #f5f5f0; }

/* SIDEBAR - FUNDO VERDE ESCURO + FONTE CLARA */
[data-testid="stSidebar"] { 
    background-color: #122e1c !important; 
}
[data-testid="stSidebar"] * {
    color: #e8f5e9 !important;
}
[data-testid="stSidebar"] h1, [data-testid="stSidebar"] h2, [data-testid="stSidebar"] h3, [data-testid="stSidebar"] p, [data-testid="stSidebar"] span, [data-testid="stSidebar"] label {
    color: #f1f8e9 !important;
}
/* Título do expander CLIENTES, FORNECEDORES */
[data-testid="stSidebar"] [data-testid="stExpander"] summary {
    background-color: #2e5a3d !important;
    border-radius: 8px;
}
[data-testid="stSidebar"] [data-testid="stExpander"] summary p {
    color: #ffffff !important;
    font-weight: 800 !important;
    font-size: 14px !important;
    letter-spacing: 0.5px;
}
/* Itens dentro: Lista, Cadastrar... */
[data-testid="stSidebar"] [data-testid="stExpander"] div[data-testid="stRadio"] label p {
    color: #dcedc8 !important;
    font-weight: 400 !important;
}
[data-testid="stSidebar"] [data-testid="stExpander"] div[data-testid="stRadio"] label[data-checked="true"] p {
    color: #ffffff !important;
    font-weight: 700 !important;
}
/* Versão e Sair no rodapé */
.sidebar-footer { margin-top: 80px; display:flex; justify-content:space-between; padding: 10px; color: #a5d6a7 !important; font-size: 12px; }

.card { background: white; border-radius: 16px; padding: 20px; box-shadow: 0 2px 12px rgba(0,0,0,0.06); border: 1px solid #eee; }
</style>
""", unsafe_allow_html=True)

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
    ws_clientes = sh.worksheet("Clientes")
    ws_fornecedores = sh.worksheet("Fornecedores")
    ws_produtos = sh.worksheet("Produtos")
    ws_cache = sh.worksheet("cache_cep")
    dados_clientes = ws_clientes.get_all_records()
    dados_forn = ws_fornecedores.get_all_records()
    df_clientes = pd.DataFrame(dados_clientes)
    df_forn = pd.DataFrame(dados_forn)
    qtd_cache = len(ws_cache.get_all_values())-1
except Exception as e:
    st.error(f"Erro: {e}")
    st.stop()

# --- TOPO ---
c1,c2,c3 = st.columns([2,3,2])
with c1:
    st.markdown('<div style="font-size:26px; font-weight:900; color:#1a2a4a;">🌱 SUBLIME <span style="background:#c5e1a5; color:#2e7d32; font-size:13px; padding:2px 8px; border-radius:6px;">V3</span><div style="font-size:18px; margin-top:-5px;">Agro</div></div>', unsafe_allow_html=True)
with c2:
    st.text_input("busca", placeholder="🔍 Buscar clientes, fornecedores, produtos...", label_visibility="collapsed")
with c3:
    st.markdown('<div style="text-align:right">🔔 ❓ <b>Ana Silva</b> ⌄ ⚙️<br><span style="font-size:12px; color:gray;">Administrador</span></div>', unsafe_allow_html=True)

# --- SIDEBAR ---
with st.sidebar:
    st.markdown('<div style="padding: 20px 10px 10px 10px;"><div style="font-size:26px; font-weight:900; color:white; line-height:1;">🌿 SUBLIME<br>AGRO</div><div style="font-size:11px; color:#a5d6a7; letter-spacing:1px; margin-top:4px;">GESTÃO AGRÍCOLA</div></div>', unsafe_allow_html=True)
    st.markdown('<div style="color:#a5d6a7; font-size:11px; font-weight:700; letter-spacing:1px; margin: 15px 0 8px 12px;">MENU</div>', unsafe_allow_html=True)
    
    with st.expander("👥 CLIENTES", expanded=True):
        menu = st.radio("menu_cli", ["• Lista", "• Cadastrar Cliente", "• Importar Planilha", "• Mapa Personalizado"], label_visibility="collapsed")
    with st.expander("🚚 FORNECEDORES", expanded=False):
        st.markdown('<p style="color:#dcedc8; font-size:13px; padding-left:10px;">• Lista<br>• Cadastrar Fornecedor<br>• Mapa Fornecedores</p>', unsafe_allow_html=True)
    with st.expander("📦 PRODUTOS", expanded=False):
        st.markdown('<p style="color:#dcedc8; font-size:13px; padding-left:10px;">• Lista<br>• Cadastrar Produto</p>', unsafe_allow_html=True)
    with st.expander("⚙️ CONFIGURAÇÕES", expanded=False):
        st.markdown('<p style="color:#dcedc8; font-size:13px; padding-left:10px;">• Limpar Cache<br>• Aparência</p>', unsafe_allow_html=True)
    
    st.markdown(f'<div class="sidebar-footer"><span>v3.1.4</span><span>⎙ Sair</span></div><div style="background:#2e7d32; color:white; padding:6px 12px; border-radius:20px; font-size:11px; margin:10px; text-align:center;">☁️ {qtd_cache} CEPs em cache</div>', unsafe_allow_html=True)

# --- CONTEÚDO ---
st.markdown(f'<div style="display:flex; justify-content:space-between; align-items:center; margin-top:10px;"><div><h1 style="margin:0; color:#1a2a4a; font-size:32px;">Gestão de Clientes & Fornecedores</h1><p style="color:#6b7280; margin:0;">Visualize no mapa e cadastre novos clientes de forma rápida</p></div><div><button style="border:1px solid #ccc; background:white; border-radius:8px; padding:8px 16px; margin-right:8px;">☰ Filtros</button><button style="background:#4a9b6b; color:white; border:none; border-radius:8px; padding:10px 18px; font-weight:700;">+ Novo Cliente</button></div></div><br>', unsafe_allow_html=True)

col_mapa, col_form = st.columns([1.7, 1])

with col_mapa:
    st.markdown('<div class="card"><h3 style="margin:0 0 12px 0; color:#1a2a4a;">Mapa de Clientes e Fornecedores</h3>', unsafe_allow_html=True)
    m = folium.Map(location=[-23.2, -45.9], zoom_start=10, tiles="CartoDB positron")
    if len(df_clientes)==0:
        for lat, lon in [(-23.15,-45.95), (-23.18,-45.93), (-23.22,-45.88), (-23.25,-45.85), (-23.1,-45.9), (-23.3,-45.8)]:
            folium.Marker([lat, lon], icon=folium.Icon(color='green', icon='leaf')).add_to(m)
        for lat, lon in [(-23.3,-45.75), (-23.31,-45.74), (-23.32,-45.73)]:
            folium.Marker([lat, lon], icon=folium.Icon(color='red')).add_to(m)
    else:
        for _, r in df_clientes.iterrows():
            folium.Marker([-23.2, -45.9], icon=folium.Icon(color='green')).add_to(m)
    st_folium(m, width=700, height=480)
    st.markdown('</div>', unsafe_allow_html=True)

with col_form:
    st.markdown('<div class="card"><h3 style="margin:0; color:#1a2a4a;">+ Cadastrar Cliente</h3><p style="color:gray; font-size:12px;">Adicione um novo cliente ao sistema</p>', unsafe_allow_html=True)
    with st.form("form_v3"):
        nome = st.text_input("Nome completo", placeholder="Ex: Fazenda São João Ltda")
        doc = st.text_input("CPF/CNPJ", placeholder="00.000.000/0000-00")
        tel = st.text_input("Telefone", placeholder="(11) 99999-9999")
        email = st.text_input("E-mail", placeholder="contato@fazenda.com.br")
        end = st.text_input("Endereço", placeholder="Rodovia SP-230, km 45")
        cA,cB = st.columns(2)
        cidade = cA.text_input("Cidade", placeholder="São José dos Campos")
        estado = cB.selectbox("Estado", ["SP","CE","MG","MT","GO","BA"])
        tipo = st.selectbox("Tipo de Cliente", ["Produtor Rural","Cooperativa","Revenda"])
        b1,b2 = st.columns(2)
        b1.form_submit_button("Limpar", use_container_width=True)
        salvar = b2.form_submit_button("✓ Salvar Cliente", type="primary", use_container_width=True)
        if salvar and nome:
            ws_clientes.append_row([nome, doc, tel, email, end, cidade, estado, tipo])
            st.success(f"✅ {nome} salvo em Clientes!")
            st.balloons()
    st.markdown('</div>', unsafe_allow_html=True)
