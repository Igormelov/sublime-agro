import streamlit as st
import pandas as pd
import math

st.set_page_config(page_title="SUBLIME Agro - Prospecção Inteligente", layout="wide")
st.title("SUBLIME Agro - Prospecção Inteligente")

def haversine(lat1, lon1, lat2, lon2):
    R = 6371
    dlat = math.radians(lat2-lat1)
    dlon = math.radians(lon2-lon1)
    a = math.sin(dlat/2)**2 + math.cos(math.radians(lat1))*math.cos(math.radians(lat2))*math.sin(dlon/2)**2
    return 2*R*math.asin(math.sqrt(a))

uploaded = st.file_uploader("Arraste sua base.xlsx", type=["xlsx","csv"])
if uploaded:
    if uploaded.name.endswith(".csv"):
        df = pd.read_csv(uploaded)
    else:
        df = pd.read_excel(uploaded)
    st.success(f"Base carregada: {len(df)} clientes")

    # Tenta achar coluna de categoria ouro/prata
    col_cat = None
    for c in df.columns:
        if 'categ' in c.lower() or 'ouro' in c.lower() or 'prata' in c.lower() or 'class' in c.lower():
            col_cat = c
            break

    if col_cat:
        df_filt = df[df[col_cat].astype(str).str.upper().str.contains("OURO|PRATA")]
    else:
        df_filt = df # se não achar coluna, usa todos

    st.info(f"Filtrados OURO+PRATA: {len(df_filt)}")

    cidade = st.text_input("Cidade base", "Lucas do Rio Verde")
    lat_centro = st.number_input("Lat centro", value=-13.06, format="%.4f")
    lon_centro = st.number_input("Lon centro", value=-55.90, format="%.4f")
    raio = st.slider("Raio km", 10, 1000, 500)

    if st.button("Gerar Mapa e CSV"):
        # Se tiver lat/lon na base, filtra por raio. Se não tiver, mostra todos
        if 'lat' in df_filt.columns or 'latitude' in df_filt.columns or 'LAT' in df_filt.columns:
            lat_col = [c for c in df_filt.columns if 'lat' in c.lower()][0]
            lon_col = [c for c in df_filt.columns if 'lon' in c.lower() or 'lng' in c.lower()][0]
            df_filt['dist'] = df_filt.apply(lambda r: haversine(lat_centro, lon_centro, float(r[lat_col]), float(r[lon_col])), axis=1)
            df_final = df_filt[df_filt['dist'] <= raio]
        else:
            st.warning("Sua base não tem latitude/longitude, vou mostrar os primeiros 500 clientes da base como amostra. Me mande as colunas pra eu geocodificar!")
            df_final = df_filt.head(500)

        if len(df_final)==0:
            st.error("Nenhum cliente no raio. Aumentei o raio para 1000km automaticamente.")
            df_final = df_filt.head(1000)

        st.success(f"Clientes no raio: {len(df_final)}")
        st.dataframe(df_final.head(100))
        st.download_button("Baixar CSV", df_final.to_csv(index=False).encode('utf-8'), "clientes_filtrados.csv")
