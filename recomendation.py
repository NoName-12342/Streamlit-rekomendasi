import pandas as pd
import datetime as dt
import streamlit as st
import matplotlib.pyplot as plt
import seaborn as sns
import plotly.express as px

# Fungsi untuk memuat data
@st.cache_data
def load_data():
    file_path = 'Most Streamed Spotify Songs 2024.csv'
    data = pd.read_csv(file_path, encoding='latin1')
    # Remove duplicate columns if any
    data = data.loc[:, ~data.columns.duplicated()]
    # Convert release date to datetime format
    data['Release Date'] = pd.to_datetime(data['Release Date'], errors='coerce')
    # Convert Spotify Streams and Shazam Counts to numeric
    data['Spotify Streams'] = pd.to_numeric(data['Spotify Streams'].astype(str).str.replace(',', ''), errors='coerce').fillna(0)
    data['Shazam Counts'] = pd.to_numeric(data['Shazam Counts'].astype(str).str.replace(',', ''), errors='coerce').fillna(0)
    data['Artist'] = data['Artist'].fillna("Unknown Artist")
    return data

# Fungsi rekomendasi lagu berdasarkan filter
def recommend_songs_by_date(data, start_date=None, end_date=None, artist=None, top_n=10, sort_by='Spotify Streams'):
    filtered_data = data.copy()
    try:
        # Ranking berdasarkan kolom yang dipilih
        filtered_data['All Time Rank'] = filtered_data[sort_by].rank(ascending=False, method='dense').fillna(0).astype('int64')

        # Filter berdasarkan artis
        if artist:
            filtered_data = filtered_data[filtered_data['Artist'].str.lower().str.contains(artist.lower())]

        # Filter data berdasarkan tanggal
        if start_date:
            filtered_data = filtered_data[filtered_data['Release Date'] >= pd.to_datetime(start_date)]
        if end_date:
            filtered_data = filtered_data[filtered_data['Release Date'] <= pd.to_datetime(end_date)]

        # Sortir dan ambil top N
        if top_n:
            filtered_data = filtered_data.nlargest(top_n, sort_by)
        else:
            filtered_data = filtered_data.sort_values(by=sort_by, ascending=False)

        # Format tampilan
        filtered_data[sort_by] = filtered_data[sort_by].apply(lambda x: '{:,.0f}'.format(x))
        return filtered_data[['Track', 'Artist', 'Album Name', 'Release Date', sort_by, 'All Time Rank']]

    except Exception as e:
        st.error(f"Error processing data: {str(e)}")
        return pd.DataFrame()

# Muat data
spotify_data = load_data()

# Streamlit app
st.title("Sistem Rekomendasi Lagu Spotify")

# Sidebar filter
st.sidebar.header("Filter Data")
artist_filter = st.sidebar.selectbox("Filter berdasarkan Artis", ["Semua Artis"] + sorted(spotify_data['Artist'].dropna().unique()), index=0)

use_date_filter = st.sidebar.checkbox("Gunakan Filter Tanggal", value=False)
if use_date_filter:
    start_date = st.sidebar.date_input(
        "Tanggal Mulai",
        value=None,  # Tidak ada tanggal awal default
        min_value=dt.date(1987, 1, 1),
        max_value=dt.date.today()
    )
    end_date = st.sidebar.date_input(
        "Tanggal Akhir",
        value=None,  # Tidak ada tanggal akhir default
        min_value=dt.date(1987, 1, 1),
        max_value=dt.date.today()
    )
else:
    start_date = None
    end_date = None

top_n = st.sidebar.number_input("Jumlah Rekomendasi (0 untuk semua)", min_value=0, value=10, step=1)

# Memuat opsi urutkan berdasarkan kolom yang ada
available_columns = ['Spotify Streams', 'Shazam Counts', 'Spotify Popularity', 'Track Score']
sort_options = [col for col in available_columns if col in spotify_data.columns]

# Dropdown "Urutkan Berdasarkan"
sort_by = st.sidebar.selectbox("Urutkan Berdasarkan", sort_options)

# Rekomendasi
recommendations = recommend_songs_by_date(
    spotify_data,
    start_date=start_date if use_date_filter else None,
    end_date=end_date if use_date_filter else None,
    artist=None if artist_filter == "Semua Artis" else artist_filter,
    top_n=top_n if top_n > 0 else None,
    sort_by=sort_by
)

if not recommendations.empty:
    st.subheader("Top Rekomendasi Lagu")
    st.dataframe(recommendations)

    # Menampilkan hasil tambahan di bawah tabel
    st.markdown("### Detail Rekomendasi")
    for i, row in recommendations.iterrows():
        st.write(f"- **Track:** {row['Track']} by {row['Artist']} (Album: {row['Album Name']})")
        st.write(f"  Released on: {row['Release Date']} | {sort_by}: {row[sort_by]} | Rank: {row['All Time Rank']}")
        st.write("---")

    # Tombol unduh
    csv = recommendations.to_csv(index=False)
    st.download_button(
        label="Download Rekomendasi sebagai CSV",
        data=csv,
        file_name='recommended_songs_by_date.csv',
        mime='text/csv',
    )
else:
    st.warning("Tidak ada rekomendasi untuk filter yang dipilih.")

# Sidebar: Tambah Data Baru
st.sidebar.header("Tambah Data Baru")
new_track = st.sidebar.text_input("Nama Lagu")
new_artist = st.sidebar.text_input("Nama Artis")
new_album = st.sidebar.text_input("Nama Album")
new_release_date = st.sidebar.date_input(
    "Tanggal Rilis",
    value=None,  # Tidak ada tanggal default
    min_value=dt.date(1987, 1, 1),
    max_value=dt.date.today()
)
new_streams = st.sidebar.number_input("Spotify Streams", min_value=0, step=1)

if st.sidebar.button("Tambahkan Data"):
    new_data = {
        'Track': new_track,
        'Artist': new_artist,
        'Album Name': new_album,
        'Release Date': pd.to_datetime(new_release_date),  # Pastikan dalam format datetime
        'Spotify Streams': new_streams
    }

    # Membuat DataFrame dari data baru
    new_data_df = pd.DataFrame([new_data])

    # Menggabungkan data lama dan data baru
    spotify_data = pd.concat([spotify_data, new_data_df], ignore_index=True)

    # Memastikan kolom 'Release Date' dalam format datetime
    spotify_data['Release Date'] = pd.to_datetime(spotify_data['Release Date'], errors='coerce')

    # Simpan data ke file
    spotify_data.to_csv('Most Streamed Spotify Songs 2024.csv', index=False)

    # Bersihkan cache dan refresh filter
    st.cache_data.clear()
    st.success("Data baru berhasil ditambahkan!")

# Visualisasi Data
st.sidebar.header("Visualisasi Data")
visualization_options = st.sidebar.selectbox(
    "Pilih Jenis Visualisasi",
    [
        "Tidak ada",
        "Histogram (Distribusi Spotify Streams)",
        "Line Chart (Tren Spotify Streams Berdasarkan Tanggal)",
        "Bar Chart (Top Artis Berdasarkan Total Streams)",
        "Pie Chart (Proporsi Streams Berdasarkan Album)"
    ]
)

# Histogram: Distribusi Spotify Streams
if visualization_options == "Histogram (Distribusi Spotify Streams)":
    st.subheader("Histogram: Distribusi Spotify Streams")
    fig, ax = plt.subplots(figsize=(10, 6))
    sns.histplot(
        spotify_data['Spotify Streams'], 
        bins=20, kde=True, color="blue", ax=ax
    )
    ax.set_title("Distribusi Spotify Streams", fontsize=16)
    ax.set_xlabel("Spotify Streams", fontsize=12)
    ax.set_ylabel("Frekuensi", fontsize=12)
    st.pyplot(fig)

# Line Chart: Tren Spotify Streams Berdasarkan Tanggal
elif visualization_options == "Line Chart (Tren Spotify Streams Berdasarkan Tanggal)":
    st.subheader("Line Chart: Tren Spotify Streams Berdasarkan Tanggal")
    trend_data = spotify_data.groupby('Release Date')['Spotify Streams'].sum().reset_index()
    trend_data = trend_data.sort_values('Release Date')
    fig = px.line(
        trend_data,
        x='Release Date',
        y='Spotify Streams',
        title="Tren Spotify Streams Berdasarkan Tanggal Rilis",
        labels={"Release Date": "Tanggal Rilis", "Spotify Streams": "Total Streams"}
    )
    st.plotly_chart(fig)

# Bar Chart: Top Artis Berdasarkan Total Streams
elif visualization_options == "Bar Chart (Top Artis Berdasarkan Total Streams)":
    st.subheader("Bar Chart: Top Artis Berdasarkan Total Streams")
    top_artists = (
        spotify_data.groupby('Artist')['Spotify Streams'].sum()
        .sort_values(ascending=False).head(10)
        .reset_index()
    )
    fig = px.bar(
        top_artists,
        x='Artist',
        y='Spotify Streams',
        title="Top 10 Artis Berdasarkan Total Streams",
        labels={"Artist": "Artis", "Spotify Streams": "Total Streams"},
        text='Spotify Streams'
    )
    fig.update_traces(texttemplate='%{text:.2s}', textposition='outside')
    fig.update_layout(xaxis_tickangle=-45)
    st.plotly_chart(fig)

# Pie Chart: Proporsi Streams Berdasarkan Album
elif visualization_options == "Pie Chart (Proporsi Streams Berdasarkan Album)":
    st.subheader("Pie Chart: Proporsi Streams Berdasarkan Album")
    album_data = (
        spotify_data.groupby('Album Name')['Spotify Streams'].sum()
        .sort_values(ascending=False).head(10)
        .reset_index()
    )
    fig = px.pie(
        album_data,
        values='Spotify Streams',
        names='Album Name',
        title="Proporsi Spotify Streams Berdasarkan Album",
        labels={"Album Name": "Nama Album", "Spotify Streams": "Total Streams"}
    )
    st.plotly_chart(fig)
