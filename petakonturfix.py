import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
from scipy.interpolate import griddata

st.set_page_config(page_title="Peta Mikrozonasi", layout="wide", page_icon="🗺️")

st.title("🗺️ Dashboard Pemetaan Spasial HVSR")
st.write("Visualisasi peta kontur dinamis dengan fitur interaktif untuk mengganti lapisan peta dasar dan arah mata angin.")
st.markdown("---")

st.sidebar.header("⚙️ Panel Unggah Data")
uploaded_file = st.sidebar.file_uploader("Unggah Data Titik HVSR (CSV):", type=["csv"])

# --- PANEL FITUR GANTI BASE MAP ---
st.sidebar.markdown("---")
st.sidebar.header("🗺️ Pengaturan Tampilan Peta")
pilihan_basemap = st.sidebar.selectbox(
    "Pilih Lapisan Peta Dasar (Base Map):",
    options=["Google Satellite", "Google Terrain", "Google Streets", "OpenStreetMap Bawaan"]
)

# Konfigurasi gaya peta berdasarkan pilihan di sidebar
style_map = "white-bg"
layers_map = []

if pilihan_basemap == "Google Satellite":
    layers_map = [{"below": 'traces', "sourcetype": "raster", "sourceattribution": "Google", "source": ["https://mt1.google.com/vt/lyrs=y&x={x}&y={y}&z={z}"]}]
elif pilihan_basemap == "Google Terrain":
    layers_map = [{"below": 'traces', "sourcetype": "raster", "sourceattribution": "Google", "source": ["https://mt1.google.com/vt/lyrs=p&x={x}&y={y}&z={z}"]}]
elif pilihan_basemap == "Google Streets":
    layers_map = [{"below": 'traces', "sourcetype": "raster", "sourceattribution": "Google", "source": ["https://mt1.google.com/vt/lyrs=m&x={x}&y={y}&z={z}"]}]
elif pilihan_basemap == "OpenStreetMap Bawaan":
    style_map = "open-street-map"

# --- KONFIGURASI ARAH MATA ANGIN (NORTH ARROW) ---
arah_angin = dict(
    source="https://upload.wikimedia.org/wikipedia/commons/thumb/9/9c/Compass_rose_simple.svg/256px-Compass_rose_simple.svg.png",
    xref="paper", yref="paper",
    x=0.98, y=0.98, # Posisi di pojok kanan atas
    sizex=0.12, sizey=0.12, # Ukuran proporsional gambar
    xanchor="right", yanchor="top",
    opacity=0.8 # Sedikit transparan agar tidak terlalu menutupi peta
)

df_hvsr = None

if uploaded_file is not None:
    try:
        df_hvsr = pd.read_csv(uploaded_file)
        df_hvsr.columns = df_hvsr.columns.str.strip()
        
        required_cols = ['Titik', 'Longitude', 'Latitude', 'f0', 'A0', 'Kg', 'tg']
        
        if all(col in df_hvsr.columns for col in required_cols):
            st.sidebar.success("✅ Data CSV Berhasil Dimuat!")
            
            parameter_pilihan = st.sidebar.selectbox("Pilih Parameter HVSR:", options=['Kg', 'f0', 'A0', 'tg'])
            metode_interpolasi = st.sidebar.radio("Metode Interpolasi:", options=['cubic', 'linear', 'nearest'], index=0)
            skema_warna = st.sidebar.selectbox("Skema Warna Kontur:", options=['Jet', 'Viridis', 'Turbo', 'RdYlBu_r'])
            
            col1, col2 = st.columns([1, 2.5])
            
            with col1:
                st.subheader("📋 Tabel Data")
                st.dataframe(df_hvsr[['Titik', 'Longitude', 'Latitude', parameter_pilihan]], use_container_width=True)
                st.info(f"**Tertinggi:** {df_hvsr[parameter_pilihan].max():.4f}\n\n**Terendah:** {df_hvsr[parameter_pilihan].min():.4f}")
            
            with col2:
                st.subheader(f"📍 Peta Kontur {parameter_pilihan}")
                
                x = df_hvsr['Longitude'].values
                y = df_hvsr['Latitude'].values
                z = df_hvsr[parameter_pilihan].values
                
                margin = 0.001
                x_grid = np.linspace(x.min() - margin, x.max() + margin, 85)
                y_grid = np.linspace(y.min() - margin, y.max() + margin, 85)
                grid_x, grid_y = np.meshgrid(x_grid, y_grid)
                grid_z = griddata((x, y), z, (grid_x, grid_y), method=metode_interpolasi)
                
                gx, gy, gz = grid_x.flatten(), grid_y.flatten(), grid_z.flatten()
                mask = ~np.isnan(gz)
                
                fig = go.Figure()
                
                fig.add_trace(go.Scattermapbox(
                    lat=gy[mask], lon=gx[mask], mode='markers',
                    marker=dict(size=14, color=gz[mask], colorscale=skema_warna, opacity=0.45),
                    name=f"Kontur {parameter_pilihan}", hoverinfo='skip'
                ))
                
                fig.add_trace(go.Scattermapbox(
                    lat=df_hvsr['Latitude'], lon=df_hvsr['Longitude'], mode='markers+text',
                    text=df_hvsr['Titik'].astype(str), textposition="top center",
                    marker=dict(size=12, color='white'), name='Stasiun',
                    hovertemplate="<b>Stasiun %{text}</b><br>Nilai: %{customdata:.4f}<extra></extra>",
                    customdata=z
                ))
                
                center_lat = y.mean()
                center_lon = x.mean()
                lon_range = x.max() - x.min()
                zoom_level = 15 if lon_range < 0.01 else 14
                
                fig.update_layout(
                    mapbox_style=style_map,
                    mapbox_layers=layers_map,
                    mapbox=dict(center=dict(lat=center_lat, lon=center_lon), zoom=zoom_level),
                    margin=dict(l=0, r=0, t=0, b=0), height=650,
                    images=[arah_angin] # <-- Memasang arah mata angin di sini
                )
                
                st.plotly_chart(fig, use_container_width=True)
        else:
            st.error(f"Gagal memuat! Pastikan file CSV memiliki kolom persis seperti ini: {required_cols}")
    except Exception as e:
        st.error(f"Terjadi kesalahan saat membaca file CSV: {e}")
else:
    st.info("💡 Sistem Siap. Silakan unggah file CSV di panel kiri untuk mulai memproses data.")
    
    fig_indo = go.Figure()
    fig_indo.update_layout(
        mapbox_style=style_map,
        mapbox_layers=layers_map,
        mapbox=dict(center=dict(lat=-2.5, lon=118.0), zoom=4),
        margin=dict(l=0, r=0, t=0, b=0), height=650,
        images=[arah_angin] # <-- Dan di peta awal yang kosong
    )
    st.plotly_chart(fig_indo, use_container_width=True)