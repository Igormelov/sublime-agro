import streamlit as st
import pandas as pd
import gspread
import folium
import requests
from datetime import datetime
from streamlit_folium import st_folium

st.set_page_config(page_title="SUBLIME Agro V3 - Dark", layout="wide")

st.markdown("""
<style>
[data-testid="stAppViewContainer"]{background:#0f1a12!important}
[data-testid="stHeader"]{background:#0f1a12!important}
[data-testid="stSidebar"]{background:#0f1a12!important; border-right:1px solid #1e3a24}
[data-testid="stSidebar"] *{color:#c8e6c9!important}

.card-dark{
 background:#1a2e1f; border:1px solid #2a4a32; border-radius:14px;
 padding:16px; box-shadow:0 4px 20px rgba(0,0,0,0.4)
}
.card-dark h4,.card-dark b{color:#e8f5e9!important}
.card-dark p,.card-dark span{color:#a5d6a7!important}

/* Inputs dark */
.stTextInput input,.stSelectbox div[data-baseweb="select"]{
 background:#122016!important; color:#e8f5e9!important;
 border:1px solid #2e5a37!important; border-radius:10px!important
}
.stTextInput input:focus{border-color:#4caf50!important}
label{color:#a5d6a7!important; font-weight:600!important}

/* Botão */
.stButton button[kind="primary"]{
 background:#2e7d32!important; color:white!important;
 border:none!important; border-radius:10px!important; font-weight:700
}

/* Topbar */
.topbar{background:#1a2e1f; border:1px solid #2a4a32; border-radius:12px; padding:12px 16px}
</style>
""", unsafe_allow_html=True)

@st.cache_resource
def get_client():
    return gspread.service_account_from_dict(dict(st.secrets["gcp_service_account"]))

@st.cache_data(ttl=60)
def load_dados():
    client = get_client()
    sh = client.open_by_key(st.secrets["SPREADSHEET_ID"])
    def get_df(nome):
        try:
            ws = sh.worksheet(nome)
            vals = ws.get_all_values()
            if len(vals) < 2: return pd.DataFrame()
            df = pd.DataFrame(vals[1:], columns=vals[0])
            # remove linhas vazias
            df = df[df.iloc[:,0]!= ""]
            return df
        except Exception as e:
            return pd.DataFrame()
    return get_df("Clientes"), get_df("Fornecedores"), get_df("Produtos"), get_df("cache_cep"), sh

def get_latlon(cep, sh):
    cep = ''.join(filter(str.isdigit, str(cep)))
    if len(cep)!=8: return None
    try:
        ws = sh.worksheet("cache_cep")
        cell = ws.find(cep)
        if cell:
            row = ws.row_values(cell.row)
            return float(row[1]), float(row[2])
    except: pass
    try:
        r = requests.get(f"https://viacep.com.br/ws/{cep}/json/", timeout=6).json()
        if "erro" in r: return None
        q = f"{r.get('logradouro','')}, {r.get('localidade','')}, {r.get('uf','')}, Brasil"
        geo = requests.get(f"https://nominatim.openstreetmap.org/search?q={q}&format=json&limit=1", headers={"User-Agent":"SublimeAgroDark"}, timeout=6).json()
        if geo:
            lat, lon = float(geo[0]['lat']), float(geo[0]['lon'])
            ws.append_row([cep, lat, lon, q, r.get('localidade',''), r.get('uf',''), datetime.now().strftime("%d/%m/%Y")])
            return lat, lon
    except: pass
    return None

try:
    df_c, df_f, df_p, df_cache, sh = load_dados()
except Exception as e:
    st.error(f"Erro: {e}")
    st.stop()

# SIDEBAR
with st.sidebar:
    st.markdown("## 🌿 SUBLIME AGRO")
    st.caption("V3 • Dark Edition")
    st.markdown("---")
    menu = st.radio("", ["● Clientes - Lista", "○ Cadastrar Cliente", "○ Fornecedores", "○ Produtos"])
    st.markdown("<br><br>", unsafe_allow_html=True)
    st.markdown(f"<div style='background:#1e3a24; padding:12px; border-radius:20px; text-align:center; border:1px solid #2e5a37'>☁️ {len(df_cache)} CEPs em cache<br><small style='color:#81c784'>{len(df_c)} clientes</small></div>", unsafe_allow_html=True)

# TOPO
c1,c2,c3 = st.columns([2,5,2])
with c1:
    st.markdown("<div class='topbar'><span style='font-weight:900; color:#e8f5e9'>🌿 SUBLIME</span> <span style='background:#2e7d32; color:white; font-size:10px; padding:2px 6px; border-radius:5px'>V3</span> <span style='color:#a5d6a7'>Agro</span></div>", unsafe_allow_html=True)
with c2:
    busca = st.text_input("", placeholder="🔍 Buscar clientes, fornecedores, produtos...", label_visibility="collapsed")
with c3:
    st.markdown(f"<div style='text-align:right; color:#e8f5e9'><b>👤 Ana Silva</b><br><span style='color:#81c784; font-size:12px'>{len(df_c)} clientes • {len(df_f)} fornecedores</span></div>", unsafe_allow_html=True)

st.markdown("<br>", unsafe_allow_html=True)

col_map, col_form = st.columns([1.7, 1])

with col_map:
    st.markdown(f"<div class='card-dark'><b style='color:#e8f5e9'>🗺️ Mapa de Clientes e Fornecedores</b> <span style='float:right; color:#81c784; font-size:12px'>{len(df_cache)} pontos</span></div>", unsafe_allow_html=True)
    # Mapa dark
    m = folium.Map(location=[-23.18, -45.88], zoom_start=10, tiles="CartoDB dark_matter")
    for _, r in df_cache.iterrows():
        try:
            lat = float(str(r[1]).replace(',','.')) if len(r)>1 else 0
            lon = float(str(r[2]).replace(',','.')) if len(r)>2 else 0
            if lat and lon:
                folium.CircleMarker([lat, lon], radius=6, color="#4caf50", fill=True, fillColor="#4caf50", fillOpacity=0.8, tooltip=str(r[0])).add_to(m)
        except: pass
    st_folium(m, width=None, height=580, returned_objects=[])

with col_form:
    st.markdown("<div class='card-dark'><h4 style='margin:0; color:#e8f5e9'>+ Cadastrar Cliente</h4><p style='font-size:12px; margin:4px 0 0 0'>Localização automática pelo CEP</p></div>", unsafe_allow_html=True)
    st.markdown("<div class='card-dark'>", unsafe_allow_html=True)
    with st.form("form_dark", clear_on_submit=True):
        nome = st.text_input("Nome*")
        razao = st.text_input("Razão Social")
        doc = st.text_input("CPF/CNPJ")
        end = st.text_input("Endereço")
        c1f, c2f = st.columns(2)
        with c1f: cep = st.text_input("CEP*")
        with c2f: cidade = st.text_input("Cidade")
        c3f, c4f = st.columns(2)
        with c3f: estado = st.selectbox("Estado", ["SP","MG","MT","GO","PR","BA","MS","TO","RS","SC"])
        with c4f: tipo = st.selectbox("Tipo_Cliente", ["Produtor Rural","Cooperativa","Revenda"])

        if st.form_submit_button("✔ Salvar Cliente", type="primary", use_container_width=True):
            if not nome or not cep:
                st.warning("Nome e CEP obrigatórios")
            else:
                latlon = get_latlon(cep, sh)
                try:
                    sh.worksheet("Clientes").append_row([len(df_c)+1, nome, razao, doc, end, cep, cidade, estado, tipo])
                    st.cache_data.clear()
                    st.success(f"✅ {nome} salvo!")
                    if latlon: st.toast(f"📍 Localizado: {latlon}")
                    st.rerun()
                except Exception as e:
                    st.error(f"Erro: {e}")
    st.markdown("</div>", unsafe_allow_html=True)
