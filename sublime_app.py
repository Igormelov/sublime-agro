import streamlit as st
import pandas as pd
import plotly.express as px
import math
from geopy.geocoders import Nominatim
import folium
from streamlit_folium import st_folium

st.set_page_config(page_title="SUBLIME Agro - Google Maps", layout="wide")
st.title("🌱 SUBLIME Agro - Mapa Google Maps")

@st.cache_data(show_spinner=False)
def geocode_city(cidade, uf=""):
    try:
        geolocator = Nominatim(user_agent="sublime_agro_v7")
        query = f"{cidade}, {uf}, Brasil" if uf else f"{cidade}, Brasil"
        loc = geolocator.geocode(query, timeout=10)
        if loc:
            return loc.latitude, loc.longitude
    except:
        pass
    return None

def haversine(lat1, lon1, lat2, lon2):
    R=6371
    dlat=math.radians(lat2-lat1); dlon=math.radians(lon2-lon1)
    a=math.sin(dlat/2)**2 + math.cos(math.radians(lat1))*math.cos(math.radians(lat2))*math.sin(dlon/2)**2
    return 2*R*math.asin(math.sqrt(a))

tab1, tab2, tab3 = st.tabs(["🗺️ Mapa Google Maps por Raio", "🏭 Fornecedores", "📦 Produtos"])

with tab1:
    up = st.file_uploader("Arraste sua planilha", type=["xlsx","csv","xls"])
    if not up:
        st.stop()

    df = pd.read_excel(up, engine='openpyxl') if up.name.endswith((".xlsx",".xls")) else pd.read_csv(up)
    df.columns = [str(c).strip() for c in df.columns]

    def find_col(nomes):
        for n in nomes:
            for c in df.columns:
                if n in c.upper():
                    return c
        return None

    col_cidade = find_col(["MUNC", "CIDADE"])
    col_uf = find_col(["ESTC", "UF", "ESTADO"])
    col_nome = find_col(["NOME", "CLIENTE"])
    col_cat = find_col(["SEGMENTO", "CATEGORIA", "OURO", "PRATA"])

    st.success(f"Base: {len(df)} | Cidade: {col_cidade} | Categoria: {col_cat}")

    st.sidebar.header("Filtros")
    df_f = df.copy()
    if col_cat:
        cats = df[col_cat].astype(str).unique().tolist()
        sel = st.sidebar.multiselect(f"Categoria ({col_cat})", cats, default=cats)
        if sel:
            df_f = df_f[df_f[col_cat].isin(sel)]

    cidades_unicas = sorted(df_f[col_cidade].dropna().astype(str).unique().tolist())
    cidade_base = st.sidebar.selectbox("📍 Cidade Base", cidades_unicas, index=cidades_unicas.index("DIVINOPOLIS") if "DIVINOPOLIS" in cidades_unicas else 0)
    raio = st.sidebar.slider("📏 Raio KM", 10, 1000, 300, 10)

    if st.sidebar.button("🔍 Buscar Cidades no Raio"):
        with st.spinner(f"Geocodificando {cidade_base} e {len(cidades_unicas)} cidades via Google/OpenStreetMap..."):
            uf_base = df_f[df_f[col_cidade]==cidade_base][col_uf].iloc[0] if col_uf else ""
            coord_base = geocode_city(cidade_base, uf_base)

            if not coord_base:
                st.error(f"Não achei {cidade_base} no mapa. Tente escrever com UF.")
                st.stop()

            st.session_state["coord_base"] = coord_base
            st.session_state["cidade_base"] = cidade_base

            dist_map = {}
            coords_map = {cidade_base: coord_base}
            for cid in cidades_unicas:
                uf_cid = df_f[df_f[col_cidade]==cid][col_uf].iloc[0] if col_uf else ""
                coord = geocode_city(cid, uf_cid)
                if coord:
                    coords_map[cid] = coord
                    d = haversine(coord_base[0], coord_base[1], coord[0], coord[1])
                    dist_map[cid] = d

            st.session_state["dist_map"] = dist_map
            st.session_state["coords_map"] = coords_map
            st.success(f"Encontradas {len(dist_map)} cidades com coordenadas!")

    if "dist_map" in st.session_state:
        dist_map = st.session_state["dist_map"]
        coords_map = st.session_state["coords_map"]
        coord_base = st.session_state["coord_base"]
        cidade_base = st.session_state["cidade_base"]

        cidades_no_raio = [c for c,d in dist_map.items() if d <= raio]
        df_final = df_f[df_f[col_cidade].astype(str).isin(cidades_no_raio)].copy()
        df_final["KM_DA_BASE"] = df_final[col_cidade].apply(lambda x: dist_map.get(x, 0))

        c1,c2,c3,c4 = st.columns(4)
        c1.metric("Clientes no Raio", len(df_final))
        c2.metric("Cidades no Raio", len(cidades_no_raio))
        c3.metric("Cidade Base", cidade_base)
        c4.metric("Raio", f"{raio} km")

        # --- MAPA GOOGLE MAPS DE VERDADE ---
        st.subheader(f"🗺️ Mapa - {len(cidades_no_raio)} cidades dentro de {raio}km de {cidade_base}")

        # Cria mapa Folium com estilo Google Maps
        m = folium.Map(location=coord_base, zoom_start=8, tiles="OpenStreetMap")

        # Marcador da cidade base em vermelho
        folium.Marker(
            coord_base,
            popup=f"<b>BASE: {cidade_base}</b>",
            icon=folium.Icon(color="red", icon="home")
        ).add_to(m)

        # Marcadores das cidades no raio
        for cid in cidades_no_raio:
            if cid == cidade_base: continue
            if cid in coords_map:
                coord = coords_map[cid]
                qtd = len(df_final[df_final[col_cidade]==cid])
                folium.Marker(
                    coord,
                    popup=f"<b>{cid}</b><br>{qtd} clientes<br>{dist_map[cid]:.0f}km da base",
                    icon=folium.Icon(color="blue", icon="user")
                ).add_to(m)

        # Círculo do raio
        folium.Circle(
            coord_base,
            radius=raio*1000,
            color="red",
            fill=True,
            fill_opacity=0.1
        ).add_to(m)

        # Mostra o mapa
        st_folium(m, width=1200, height=600)

        # Link para abrir no Google Maps de verdade
        st.markdown("### 📱 Abrir no Google Maps")
        st.markdown(f"[🔗 Abrir {cidade_base} no Google Maps](https://www.google.com/maps/search/?api=1&query={cidade_base})")
        # Link com todas as cidades
        for cid in cidades_no_raio[:5]:
            st.markdown(f"[📍 Ver clientes em {cid} no Google Maps](https://www.google.com/maps/search/?api=1&query={cid})")

        st.divider()
        st.dataframe(df_final, use_container_width=True, height=500)
        st.download_button("📥 Baixar CSV", df_final.to_csv(index=False).encode('utf-8'), f"clientes_{cidade_base}_{raio}km.csv")

with tab2:
    st.header("Fornecedores")
    st.info("Cadastro de fornecedores - em breve com Google Sheets")

with tab3:
    st.header("Produtos por Fornecedor")
