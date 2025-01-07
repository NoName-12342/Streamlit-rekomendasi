import pandas as pd
import datetime as dt
import streamlit as st

# Load the dataset
@st.cache_data
def load_data():
    file_path = 'Most Streamed Spotify Songs 2024.csv'
    data = pd.read_csv(file_path, encoding='latin1')
    # Remove duplicate columns if any
    data = data.loc[:, ~data.columns.duplicated()]
    # Convert release date to datetime format
    data['Release Date'] = pd.to_datetime(data['Release Date'], errors='coerce')
    # Convert Spotify Streams to numeric, handling any non-numeric values
    data['Spotify Streams'] = pd.to_numeric(data['Spotify Streams'].astype(str).str.replace(',', ''), errors='coerce').fillna(0)
    # Convert Spotify Popularity to numeric if it exists
    if 'Spotify Popularity' in data.columns:
        data['Spotify Popularity'] = pd.to_numeric(data['Spotify Popularity'], errors='coerce').fillna(0)
    # Fill NaN values in Artist column with "Unknown Artist"
    data['Artist'] = data['Artist'].fillna("Unknown Artist")
    return data

def recommend_songs_by_date(data, start_date=None, end_date=None, artist=None, top_n=10, sort_by='Spotify Streams'):
    # Create a copy of the data to avoid modifying the original
    filtered_data = data.copy()
    
    try:
        # Handle the sorting column
        if sort_by != 'Spotify Streams' and sort_by != 'Spotify Popularity':  # Only convert if not already converted
            filtered_data[sort_by] = pd.to_numeric(
                filtered_data[sort_by].astype(str).str.replace(',', ''),
                errors='coerce'
            ).fillna(0)
        
        # Calculate All Time Rank based on the complete dataset before filtering
        filtered_data['All Time Rank'] = filtered_data[sort_by].rank(
            ascending=False,
            method='dense'
        ).fillna(0).astype('int64')
        
        # Filter by artist if provided
        if artist:
            filtered_data = filtered_data[filtered_data['Artist'].str.lower().str.contains(artist.lower())]
        
        # Filter data based on dates only if dates are provided
        if start_date is not None:
            filtered_data = filtered_data[filtered_data['Release Date'] >= pd.to_datetime(start_date)]
        if end_date is not None:
            filtered_data = filtered_data[filtered_data['Release Date'] <= pd.to_datetime(end_date)]
        
        # Sort data and get top N records
        if top_n:
            filtered_data = filtered_data.nlargest(top_n, sort_by)
        else:
            filtered_data = filtered_data.sort_values(by=sort_by, ascending=False)
        
        # Format streams for display
        if sort_by == 'Spotify Streams':
            filtered_data[sort_by] = filtered_data[sort_by].apply(lambda x: '{:,.0f}'.format(x))
        elif sort_by == 'Spotify Popularity':
            filtered_data[sort_by] = filtered_data[sort_by].apply(lambda x: '{:.1f}'.format(x))
        else:
            filtered_data[sort_by] = filtered_data[sort_by].apply(lambda x: '{:,.0f}'.format(x))
        
        columns_to_display = ['Track', 'Artist', 'Album Name', 'Release Date', sort_by, 'All Time Rank']
        if sort_by != 'Spotify Popularity' and 'Spotify Popularity' in filtered_data.columns:
            columns_to_display.insert(-1, 'Spotify Popularity')
            
        return filtered_data[columns_to_display]
    
    except Exception as e:
        st.error(f"Error processing data: {str(e)}")
        return pd.DataFrame()

# Load data
spotify_data = load_data()

# Get unique artists for the dropdown, handling NaN values
artists = sorted([artist for artist in spotify_data['Artist'].unique() if pd.notna(artist)])

# Streamlit app
st.title("Spotify Song Recommendation System")

# Sidebar filters
st.sidebar.header("Filter Options")

# Artist filter
artist_filter = st.sidebar.selectbox(
    "Filter by Artist",
    options=["All Artists"] + list(artists),
    index=0
)

# Create a checkbox to enable/disable date filtering
use_date_filter = st.sidebar.checkbox("Use Date Filter", value=False)

if use_date_filter:
    # Set min and max dates
    min_date = dt.date(1987, 1, 1)
    max_date = dt.date.today()
    
    # Date inputs with calendar
    start_date = st.sidebar.date_input(
        "Start Date",
        value=None,
        min_value=min_date,
        max_value=max_date,
        key="start_date"
    )
    
    end_date = st.sidebar.date_input(
        "End Date",
        value=None,
        min_value=min_date,
        max_value=max_date,
        key="end_date"
    )
else:
    start_date = None
    end_date = None

top_n = st.sidebar.number_input("Number of Recommendations (0 for all)", min_value=0, value=10, step=1)

# Add Spotify Popularity to sorting options
sort_options = ['Spotify Streams', 'Track Score', 'Spotify Playlist Count', 'Shazam Counts']
if 'Spotify Popularity' in spotify_data.columns:
    sort_options.insert(1, 'Spotify Popularity')

sort_by = st.sidebar.selectbox(
    "Sort Recommendations By", 
    options=sort_options
)

# Generate recommendations
recommendations = recommend_songs_by_date(
    spotify_data,
    start_date=start_date if use_date_filter else None,
    end_date=end_date if use_date_filter else None,
    artist=None if artist_filter == "All Artists" else artist_filter,
    top_n=top_n if top_n > 0 else None,
    sort_by=sort_by
)

# Display recommendations
if not recommendations.empty:
    st.subheader("Top Recommended Songs")
    st.dataframe(recommendations)

    # Menampilkan hasil tambahan di bawah tabel
    st.markdown("### Detail Rekomendasi")
    for i, row in recommendations.iterrows():
        st.write(f"- **Track:** {row['Track']} by {row['Artist']} (Album: {row['Album Name']})")
        st.write(f"  Released on: {row['Release Date']} | {sort_by}: {row[sort_by]} | Rank: {row['All Time Rank']}")
        st.write("---")

    # Download option
    csv = recommendations.to_csv(index=False)
    st.download_button(
        label="Download Recommendations as CSV",
        data=csv,
        file_name='recommended_songs_by_date.csv',
        mime='text/csv',
    )
else:
    st.warning("No recommendations found for the selected criteria.")
