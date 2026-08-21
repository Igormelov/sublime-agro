import streamlit as st
import pandas as pd
import gspread
from google.oauth2.service_account import Credentials
import folium
from streamlit_folium import st_folium

st.set_page_config(page_title="SUBLIME Agro V3", layout="wide", initial_sidebar_state="expanded")

# --- CSS CLONE EXATO DA FOTO ---
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;600;700;800&display=swap');
* { font-family: 'Inter', sans-serif; }
[data-testid="stHeader"] { display:none; }
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;600;700;800&display=swap');
* { font-family: 'Inter', sans-serif; }
[data-testid="stHeader"] { display:none; }

/* SIDEBAR VERDE ESCURO COM FONTE BRANCA */
[data-testid="stSidebar"] { 
    background-color: #1a3a2a !important; 
    padding-top: 0 !important; 
}
[data-testid="stSidebar"] * {
    color: #FFFFFF !important;
}
[data-testid="stSidebar"] .stExpander summary p {
    color: #FFFFFF !important;
    font-weight: 700 !important;
    font-size: 15px !important;
}
[data-testid="stSidebar"] .stRadio label p {
    color: #FFFFFF !important;
    font-size: 14px !important;
}
[data-testid="stSidebar"] label[data-baseweb="radio"] div p {
    color: white !important;
}

.main { background-color: #f5f5f0; }
.top-bar { background: white; border-radius: 16px; padding: 12px 20px; display: flex; align-items: center; justify-content: space-between; margin-bottom: 20px; box-shadow: 0 1px 3px rgba(0,0,0,0.08); }
.logo { font-size: 28px; font-weight: 800; color: #1a2a4a; line-height: 1; }
.logo span { background: #c5e1a5; color: #2e7d32; font-size: 14px; padding: 2px 8px; border-radius: 6px; margin-left: 8px; vertical-align: middle; }
.card { background: white; border-radius: 16px; padding: 20px; box-shadow: 0 2px 12px rgba(0,0,0,0.06); border: 1px solid #eee; }
</style>
""", unsafe_allow_html=True)
.main { background-color: #f5f5f0; }
.top-bar { background: white; border-radius: 16px; padding: 12px 20px; display: flex; align-items: center; justify-content: space-between; margin-bottom: 20px; box-shadow: 0 1px 3px rgba(0,0,0,0.08); }
.logo { font-size: 28px; font-weight: 800; color: #1a2a4a; line-height: 1; }
.logo span { background: #c5e1a5; color: #2e7d32; font-size: 14px; padding: 2px 8px; border-radius: 6px; margin-left: 8px; vertical-align: middle; }
.search-box { background: #f0f0f0; border-radius: 24px; padding: 8px 16px; width: 400px; border: none; }
.card { background: white; border-radius: 16px; padding: 20px; box-shadow: 0 2px 12px rgba(0,0,0,0.06); border: 1px solid #eee; }
.menu-section { color: #8fbc8f; font-size: 12px; font-weight: 700; letter-spacing: 1px; margin-top: 20px; margin-bottom: 8px; }
.menu-active { background-color: #6b9b6b !important; color: white !important; border-radius: 8px; padding: 10px 12px; font-weight: 600; }
.menu-item { padding: 6px 12px 6px 24px; color: #c8e6c9; font-size: 14px; cursor: pointer; }
.btn-green { background-color: #4a9b6b; color: white; border-radius: 8px; border: none; padding: 10px 20px; font-weight: 600; }
</style>
""", unsafe_allow_html=True)

# --- CONEXÃO PLANILHA ---
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

# --- TOP BAR ---
col_logo, col_search, col_user = st.columns([2,3,2])
with col_logo:
    st.markdown('<div class="logo">🌱 SUBLIME<span>V3</span><br><div style="font-size:18px; margin-left:28px; margin-top:-4px;">Agro</div></div>', unsafe_allow_html=True)
with col_search:
    st.text_input("search", placeholder="🔍 Buscar clientes, fornecedores, produtos...", label_visibility="collapsed")
with col_user:
    st.markdown('<div style="text-align:right">🔔 ❓ <img src="https://i.pravatar.cc/40?img=5" style="border-radius:50%; width:36px; vertical-align:middle;"> <b>Ana Silva</b> ⌄ ⚙️<br><span style="font-size:12px; color:gray;">Administrador</span></div>', unsafe_allow_html=True)

# --- SIDEBAR ---
with st.sidebar:
    st.markdown('<div style="color:#7fb07f; font-size:12px; font-weight:700; letter-spacing:1px; margin: 20px 0 10px 10px;">MENU</div>', unsafe_allow_html=True)
    
    with st.expander("👥 CLIENTES", expanded=True):
        menu_clientes = st.radio("c", ["• Lista", "• Cadastrar Cliente", "• Importar Planilha", "• Mapa Personalizado"], label_visibility="collapsed")
    with st.expander("🚚 FORNECEDORES", expanded=False):
        st.write("• Lista\n• Cadastrar Fornecedor\n• Mapa Fornecedores")
    with st.expander("📦 PRODUTOS", expanded=False):
        st.write("• Lista\n• Cadastrar Produto")
    with st.expander("⚙️ CONFIGURAÇÕES", expanded=False):
        st.write("• Limpar Cache\n• Aparência")
    
    st.markdown('<div style="margin-top:100px; display:flex; justify-content:space-between; padding: 0 10px; color:#7fb07f; font-size:12px;"><span>v3.1.4</span><span>⎙ Sair</span></div>', unsafe_allow_html=True)

# --- CONTEÚDO PRINCIPAL ---
st.markdown(f'<div style="display:flex; justify-content:space-between; align-items:center;"><div><h1 style="margin:0; color:#1a2a4a;">Gestão de Clientes & Fornecedores</h1><p style="color:gray; margin:0;">Visualize no mapa e cadastre novos clientes de forma rápida • {qtd_cache} CEPs em cache</p></div><div><button style="border:1px solid #ccc; background:white; border-radius:8px; padding:8px 16px; margin-right:8px;">☰ Filtros</button><button style="background:#4a9b6b; color:white; border:none; border-radius:8px; padding:8px 16px; font-weight:600;">+ Novo Cliente</button></div></div>', unsafe_allow_html=True)

st.markdown("<br>", unsafe_allow_html=True)

col_mapa, col_form = st.columns([1.6, 1])

with col_mapa:
    st.markdown('<div class="card">', unsafe_allow_html=True)
    st.markdown(f'<h3 style="margin:0 0 12px 0;">Mapa de Clientes e Fornecedores</h3>')
    
    # Mapa Folium com pins verdes e vermelhos igual da foto
    m = folium.Map(location=[-23.2, -45.9], zoom_start=10, tiles="CartoDB positron")
    
    # Adiciona clientes (verde) - pega da planilha se tiver lat/lon
    for _, row in df_clientes.head(30).iterrows():
        try:
            lat = float(str(row.get('latitude','')).replace(',','.')) if row.get('latitude') else -23.2 + (hash(row.get('nome',''))%100)/500
            lon = float(str(row.get('longitude','')).replace(',','.')) if row.get('longitude') else -45.9 + (hash(row.get('nome',''))%100)/500
            folium.Marker([lat, lon], icon=folium.Icon(color='green', icon='leaf')).add_to(m)
        except:
            pass
    
    # Adiciona fornecedores (vermelho)
    for _, row in df_forn.head(20).iterrows():
        folium.Marker([-23.2 + 0.05, -45.8 + 0.05], icon=folium.Icon(color='red')).add_to(m)
    
    # Se planilha vazia, mostra pins demo iguais da foto
    if len(df_clientes)==0:
        for lat, lon in [(-23.15,-45.95), (-23.18,-45.93), (-23.22,-45.88), (-23.25,-45.85), (-23.1,-45.9)]:
            folium.Marker([lat, lon], icon=folium.Icon(color='green')).add_to(m)
        for lat, lon in [(-23.3,-45.75), (-23.31,-45.74), (-23.32,-45.73)]:
            folium.Marker([lat, lon], icon=folium.Icon(color='red')).add_to(m)

    st_folium(m, width=700, height=500)
    
    st.markdown(f'<div style="display:flex; gap:10px; font-size:12px;"><div style="background:white; border:1px solid #ddd; border-radius:8px; padding:8px;">🟢 Clientes ({len(df_clientes) if len(df_clientes)>0 else 142})<br>🔴 Fornecedores ({len(df_forn) if len(df_forn)>0 else 38})</div><div style="margin-left:auto; background:white; border:1px solid #ddd; border-radius:8px; padding:8px;">12 clientes ativos na região •<br>5 fornecedores próximos</div></div>', unsafe_allow_html=True)
    st.markdown('</div>', unsafe_allow_html=True)

with col_form:
    st.markdown('<div class="card">', unsafe_allow_html=True)
    st.markdown('<h3 style="margin:0;">+ Cadastrar Cliente</h3><p style="color:gray; font-size:13px; margin:0 0 15px 0;">Adicione um novo cliente ao sistema</p>', unsafe_allow_html=True)
    
    with st.form("cadastro_igual_foto"):
        st.markdown("**Nome completo**")
        nome = st.text_input("nome", placeholder="Ex: Fazenda São João Ltda", label_visibility="collapsed")
        st.markdown("**CPF/CNPJ**")
        doc = st.text_input("doc", placeholder="00.000.000/0000-00", label_visibility="collapsed")
        st.markdown("**Telefone**")
        tel = st.text_input("tel", placeholder="(11) 99999-9999", label_visibility="collapsed")
        st.markdown("**E-mail**")
        email = st.text_input("email", placeholder="contato@fazenda.com.br", label_visibility="collapsed")
        st.markdown("**Endereço**")
        end = st.text_input("end", placeholder="Rodovia SP-230, km 45", label_visibility="collapsed")
        c1,c2 = st.columns(2)
        with c1:
            st.markdown("**Cidade**")
            cidade = st.text_input("cidade", placeholder="São José dos Campos", label_visibility="collapsed")
        with c2:
            st.markdown("**Estado**")
            estado = st.selectbox("estado", ["SP","CE","MG","MT","GO","BA"], label_visibility="collapsed")
        st.markdown("**Tipo de Cliente**")
        tipo = st.selectbox("tipo", ["Produtor Rural","Cooperativa","Revenda","Indústria"], label_visibility="collapsed")
        
        b1,b2 = st.columns(2)
        with b1:
            st.form_submit_button("Limpar", use_container_width=True)
        with b2:
            salvar = st.form_submit_button("✓ Salvar Cliente", type="primary", use_container_width=True)
        
        if salvar:
            if nome:
                ws_clientes.append_row([nome, doc, tel, email, end, cidade, estado, tipo])
                st.success(f"✅ {nome} salvo! Já aparece como pin verde no mapa.")
                st.balloons()
            else:
                st.error("Digite o nome completo")
    
    st.markdown('</div>', unsafe_allow_html=True)
    st.caption("Os dados serão salvos e o cliente aparecerá no mapa como pin verde.")
