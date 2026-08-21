import streamlit as st
import pandas as pd
import gspread
import folium
import requests
from datetime import datetime
from streamlit_folium import st_folium
from google.oauth2.service_account import Credentials

st.set_page_config(page_title="SUBLIME Agro V3", layout="wide", initial_sidebar_state="expanded")

st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;600;700;900&display=swap');
* {font-family:'Inter',sans-serif}
[data-testid="stHeader"]{display:none}
[data-testid="stAppViewContainer"]{background:#f2f2ed}
[data-testid="stSidebar"]{background:#1a3a2a!important}
[data-testid="stSidebar"] *{color:#e8f5e9!important}
.card{background:white; border-radius:16px; padding:18px; box-shadow:0 2px 14px rgba(0,0,0,0.06); border:1px solid #eee}
</style>
""", unsafe_allow_html=True)

@st.cache_resource
def conecta():
    creds = Credentials.from_service_account_info(dict(st.secrets["gcp_service_account"]),
        scopes=["https://www.googleapis.com/auth/spreadsheets","https://www.googleapis.com/auth/drive"])
    return gspread.authorize(creds).open_by_key(st.secrets["SPREADSHEET_ID"])

@st.cache_data(ttl=300, show_spinner=False)
def load_tudo():
    sh = conecta()
    def get_df(nome):
        try: return pd.DataFrame(sh.worksheet(nome).get_all_records())
        except: return pd.DataFrame()
    return get_df("Clientes"), get_df("Fornecedores"), get_df("Produtos"), get_df("cache_cep"), sh

def buscar_lat_lon(cep, sh):
    cep_limpo = ''.join(filter(str.isdigit, cep))
    ws_cache = sh.worksheet("cache_cep")
    # 1. Tenta no cache
    try:
        cell = ws_cache.find(cep_limpo)
        row = ws_cache.row_values(cell.row)
        return float(row[1]), float(row[2]), row[3], row[4], row[5]
    except: pass
    # 2. Busca no ViaCEP + Nominatim
    try:
        r = requests.get(f"https://viacep.com.br/ws/{cep_limpo}/json/", timeout=5).json()
        endereco = f"{r.get('logradouro','')}, {r.get('localidade','')}, {r.get('uf','')}"
        cidade = r.get('localidade',''); estado = r.get('uf','')
        geo = requests.get(f"https://nominatim.openstreetmap.org/search?q={endereco}&format=json&limit=1", headers={"User-Agent":"SublimeAgro"}, timeout=5).json()
        if geo:
            lat, lon = float(geo[0]['lat']), float(geo[0]['lon'])
            ws_cache.append_row([cep_limpo, lat, lon, endereco, cidade, estado, datetime.now().strftime("%d/%m/%Y")])
            return lat, lon, endereco, cidade, estado
    except: pass
    return -23.2, -45.9, "", "", ""

try:
    df_c, df_f, df_p, df_cache, sh = load_tudo()
    ws_c = sh.worksheet("Clientes")
except Exception as e:
    st.error(f"Erro: {e}"); st.stop()

# TOPO
c1,c2,c3 = st.columns([2,4,2])
with c1: st.markdown('<div style="font-weight:900; font-size:22px;">🌿 SUBLIME <span style="background:#c5e1a5; color:#2e7d32; font-size:11px; padding:3px 7px; border-radius:6px;">V3</span> Agro</div>', unsafe_allow_html=True)
with c2: st.text_input("busca", placeholder="🔍 Buscar clientes, fornecedores, produtos...", label_visibility="collapsed")
with c3: st.markdown('<div style="text-align:right"><b>Ana Silva</b> ⌄</div>', unsafe_allow_html=True)

# SIDEBAR
with st.sidebar:
    st.markdown('<p style="font-size:11px; opacity:0.7;">MENU</p>', unsafe_allow_html=True)
    st.markdown('<div style="background:#4a7a5a; padding:10px; border-radius:8px; font-weight:800;">👥 CLIENTES</div>', unsafe_allow_html=True)
    st.markdown('<div style="line-height:2.2; padding-left:10px; font-size:14px;">• Lista<br>• <b>Cadastrar Cliente</b><br>• Importar Planilha<br>• Mapa Personalizado<br><br>🚚 FORNECEDORES<br>• Lista<br>• Cadastrar Fornecedor<br><br>📦 PRODUTOS<br>• Lista<br>• Cadastrar Produto<br><br>⚙️ CONFIGURAÇÕES<br>• Limpar Cache</div>', unsafe_allow_html=True)
    st.markdown(f'<br><div style="background:#2e7d32; padding:8px; border-radius:20px; text-align:center; font-size:12px;">☁️ {len(df_cache)} CEPs em cache</div>', unsafe_allow_html=True)

st.markdown('## Gestão de Clientes & Fornecedores')
st.caption(f"Visualize no mapa e cadastre novos clientes de forma rápida • {len(df_c)} clientes • {len(df_f)} fornecedores")

col_mapa, col_form = st.columns([1.8, 1])

with col_mapa:
    st.markdown('<div class="card"><b>Mapa de Clientes e Fornecedores</b>', unsafe_allow_html=True)
    m = folium.Map(location=[-23.2, -45.9], zoom_start=10, tiles="CartoDB positron")
    # Pinos clientes do cache
    for _, r in df_cache.iterrows():
        try: folium.Marker([float(r['lat']), float(r['lon'])], tooltip=str(r['endereco_completo']), icon=folium.Icon(color='green', icon='leaf')).add_to(m)
        except: pass
    st_folium(m, width=700, height=520)
    st.markdown('</div>', unsafe_allow_html=True)

with col_form:
    st.markdown('<div class="card"><h3>+ Cadastrar Cliente</h3><p style="font-size:12px; color:gray;">Adicione um novo cliente ao sistema</p>', unsafe_allow_html=True)
    with st.form("cad_cli"):
        nome = st.text_input("Nome completo", placeholder="Ex: Fazenda São João")
        razao = st.text_input("Razão Social", placeholder="Fazenda São João Ltda")
        doc = st.text_input("CPF/CNPJ", placeholder="00.000.000/0000-00")
        endereco = st.text_input("Endereço", placeholder="Rodovia SP-230, km 45")
        cep = st.text_input("CEP", placeholder="12200-000")
        c1,c2 = st.columns(2)
        cidade = c1.text_input("Cidade", placeholder="São José dos Campos")
        estado = c2.selectbox("Estado", ["SP","MG","MT","GO","PR","BA","Outros"])
        tipo = st.selectbox("Tipo de Cliente", ["Produtor Rural","Cooperativa","Revenda","Outros"])
        salvar = st.form_submit_button("✔ Salvar Cliente", type="primary", use_container_width=True)
        if salvar:
            if not nome or not cep:
                st.error("Preencha Nome e CEP")
            else:
                with st.spinner("Buscando CEP e salvando..."):
                    lat, lon, end_comp, cid_via, est_via = buscar_lat_lon(cep, sh)
                    if not cidade: cidade = cid_via
                    if not endereco: endereco = end_comp
                    novo_id = len(df_c) + 1 if not df_c.empty else 1
                    ws_c.append_row([novo_id, nome, razao, doc, endereco, cep, cidade, estado, tipo])
                    st.cache_data.clear()
                    st.success(f"✅ {nome} salvo! Pin verde criado.")
                    st.rerun()
    st.markdown('</div>', unsafe_allow_html=True)
    st.caption("Os dados serão salvos e o cliente aparecerá no mapa como pin verde.")

with st.expander("👀 Ver dados atuais da sua planilha"):
    st.write("**Clientes:**", df_c)
    st.write("**Fornecedores:**", df_f)
    st.write("**Produtos:**", df_p)
