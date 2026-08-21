import streamlit as st
import pandas as pd
import gspread
import folium
import requests
from datetime import datetime
from streamlit_folium import st_folium

st.set_page_config(page_title="SUBLIME Agro V3", layout="wide")

st.markdown("""
<style>
[data-testid="stHeader"]{display:none}
[data-testid="stAppViewContainer"]{background:#f2f2ed}
[data-testid="stSidebar"]{background:#1a3a2a!important}
[data-testid="stSidebar"] *{color:#e8f5e9!important}
.card{background:white; border-radius:16px; padding:18px; box-shadow:0 2px 14px rgba(0,0,0,0.06)}
</style>
""", unsafe_allow_html=True)

# --- CONEXÃO QUE CORRIGE O ERRO _auth_request ---
@st.cache_resource
def get_client():
    # Este método não usa AuthorizedSession com bug
    return gspread.service_account_from_dict(dict(st.secrets["gcp_service_account"]))

@st.cache_data(ttl=300, show_spinner=False)
def load_tudo():
    client = get_client()
    sh = client.open_by_key(st.secrets["SPREADSHEET_ID"])
    def get_df(nome):
        try: return pd.DataFrame(sh.worksheet(nome).get_all_records())
        except: return pd.DataFrame()
    return get_df("Clientes"), get_df("Fornecedores"), get_df("Produtos"), get_df("cache_cep"), sh

def buscar_lat_lon(cep, sh):
    cep_limpo = ''.join(filter(str.isdigit, cep))
    ws_cache = sh.worksheet("cache_cep")
    try:
        cell = ws_cache.find(cep_limpo)
        row = ws_cache.row_values(cell.row)
        return float(row[1]), float(row[2])
    except: pass
    try:
        r = requests.get(f"https://viacep.com.br/ws/{cep_limpo}/json/", timeout=5).json()
        endereco = f"{r.get('logradouro','')}, {r.get('localidade','')}, {r.get('uf','')}"
        geo = requests.get(f"https://nominatim.openstreetmap.org/search?q={endereco}&format=json&limit=1", headers={"User-Agent":"SublimeAgro"}, timeout=5).json()
        if geo:
            lat, lon = float(geo[0]['lat']), float(geo[0]['lon'])
            ws_cache.append_row([cep_limpo, lat, lon, endereco, r.get('localidade',''), r.get('uf',''), datetime.now().strftime("%d/%m/%Y")])
            return lat, lon
    except: pass
    return -23.2, -45.9

try:
    df_c, df_f, df_p, df_cache, sh = load_tudo()
except Exception as e:
    st.error(f"Erro ao conectar planilha: {e}")
    st.info("Verifique se compartilhou a planilha com o e-mail do service account")
    st.stop()

# TOPO
c1,c2,c3 = st.columns([2,4,2])
with c1: st.markdown('<div style="font-weight:900;">🌿 SUBLIME <span style="background:#c5e1a5; color:#2e7d32; font-size:11px; padding:3px 7px; border-radius:6px;">V3</span> Agro</div>', unsafe_allow_html=True)
with c2: st.text_input("busca", placeholder="🔍 Buscar clientes, fornecedores, produtos...", label_visibility="collapsed")
with c3: st.markdown(f'<div style="text-align:right">👤 Ana Silva<br><small>{len(df_c)} clientes</small></div>', unsafe_allow_html=True)

with st.sidebar:
    st.markdown('### 🌿 SUBLIME AGRO')
    st.radio("MENU", ["👥 Clientes - Lista", "👥 Cadastrar Cliente", "🚚 Fornecedores", "📦 Produtos"], label_visibility="collapsed")
    st.markdown(f'<br><div style="background:#2e7d32; padding:8px; border-radius:20px; text-align:center; font-size:12px;">☁️ {len(df_cache)} CEPs em cache</div>', unsafe_allow_html=True)

col_mapa, col_form = st.columns([1.8,1])
with col_mapa:
    st.markdown('<div class="card"><b>Mapa de Clientes e Fornecedores</b>', unsafe_allow_html=True)
    m = folium.Map(location=[-23.2, -45.9], zoom_start=11, tiles="CartoDB positron")
    for _, r in df_cache.iterrows():
        try: folium.Marker([float(r['lat']), float(r['lon'])], icon=folium.Icon(color='green')).add_to(m)
        except: pass
    st_folium(m, width=700, height=520)
    st.markdown('</div>', unsafe_allow_html=True)

with col_form:
    st.markdown('<div class="card"><h3>+ Cadastrar Cliente</h3></div>', unsafe_allow_html=True)
    with st.form("cad"):
        nome = st.text_input("Nome")
        razao = st.text_input("Razão Social")
        doc = st.text_input("CPF/CNPJ")
        end = st.text_input("Endereço")
        cep = st.text_input("CEP")
        cidade = st.text_input("Cidade")
        estado = st.selectbox("Estado", ["SP","MG","MT","GO","PR","BA"])
        tipo = st.selectbox("Tipo_Cliente", ["Produtor Rural","Cooperativa","Revenda"])
        if st.form_submit_button("✔ Salvar Cliente", type="primary", use_container_width=True):
            if nome and cep:
                lat, lon = buscar_lat_lon(cep, sh)
                sh.worksheet("Clientes").append_row([len(df_c)+1, nome, razao, doc, end, cep, cidade, estado, tipo])
                st.cache_data.clear()
                st.success(f"✅ {nome} salvo!")
                st.rerun()
