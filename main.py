import streamlit as st
import pandas as pd
from anthropic import Anthropic
import json
from datetime import datetime
import os

anthropic_client = Anthropic(api_key=os.environ["ANTHROPIC_API_KEY"])

def adjust_section_times(duration):
    if duration == "45":
        return {
            "Grounding & Warm Up": "5-7",
            "Sun Salutations": "2-3",
            "Movement Series 1": "6-8",
            "Movement Series 2": "8-10",
            "Integration Series": "6-8",
            "Savasana": "5-7"
        }
    elif duration == "75":
        return {
            "Grounding & Warm Up": "10-12",
            "Sun Salutations": "3-4",
            "Movement Series 1": "12-15",
            "Movement Series 2": "15-17",
            "Integration Series": "12-15",
            "Savasana": "10-12"
        }
    else:  # 60 minutes
        return {
            "Grounding & Warm Up": "8-10",
            "Sun Salutations": "2-3",
            "Movement Series 1": "8-10",
            "Movement Series 2": "10-12",
            "Integration Series": "8-10",
            "Savasana": "8-10"
        }

def get_claude_recommendations(theme, class_duration):
    section_times = adjust_section_times(class_duration)
    
    # Create a template for each section's JSON structure
    section_template = """
        "%s": {
            "duration": "%s minutes",
            "section_intensity": "%s",
            "songs": [
                {
                    "name": "Example Song",
                    "artist": "Example Artist",
                    "length": "03:30",
                    "intensity": %d,
                    "reason": "Example reason",
                    "spotify_url": "https://open.spotify.com/track/example",
                    "youtube_url": "https://youtube.com/watch?v=example"
                }
            ]
        }"""
    
    # Build the sections object with proper formatting
    sections = {
        "Grounding & Warm Up": {"duration": section_times["Grounding & Warm Up"], "intensity": "1-2"},
        "Sun Salutations": {"duration": section_times["Sun Salutations"], "intensity": "1-3"},
        "Movement Series 1": {"duration": section_times["Movement Series 1"], "intensity": "2-3"},
        "Movement Series 2": {"duration": section_times["Movement Series 2"], "intensity": "2-4"},
        "Integration Series": {"duration": section_times["Integration Series"], "intensity": "2-4"},
        "Savasana": {"duration": section_times["Savasana"], "intensity": "1-2"}
    }
    
    # Build the complete prompt with properly formatted JSON
    sections_json = ",\n".join(
        section_template % (
            name,
            details["duration"],
            details["intensity"],
            int(details["intensity"].split("-")[0])
        )
        for name, details in sections.items()
    )
    
    prompt = f"""Create a playlist for a {class_duration}-minute yoga class with theme: {theme}. 
    Return a JSON object with this exact structure (replace example values):
    
    {{
        "sections": {{
            {sections_json}
        }}
    }}
    
    For each section:
    - Include 2-3 songs that fit within the section's time limit
    - Match song intensities (1-5) to section_intensity range
    - Use MM:SS format for length
    - Include brief reason why the song fits
    - Include valid Spotify and YouTube URLs for each song
    """

    try:
        message = anthropic_client.beta.messages.create(
            model="claude-3-sonnet-20240229",
            max_tokens=1500,
            temperature=0.7,
            system="You are a yoga music expert. Provide real songs with actual Spotify and YouTube URLs. Respond only with valid JSON.",
            messages=[{"role": "user", "content": prompt}]
        )
        
        # Add error handling for JSON parsing
        try:
            result = json.loads(message.content[0].text)
            return result
        except json.JSONDecodeError as e:
            # Extract just the JSON portion if there's extra text
            json_start = message.content[0].text.find("{")
            json_end = message.content[0].text.rfind("}") + 1
            if json_start >= 0 and json_end > json_start:
                json_str = message.content[0].text[json_start:json_end]
                return json.loads(json_str)
            else:
                raise e
            
    except Exception as e:
        st.error(f"Error getting recommendations: {str(e)}")
        return None

def calculate_duration(length_str):
    minutes, seconds = map(int, length_str.split(':'))
    return minutes * 60 + seconds

def main():
    st.set_page_config(page_title="Yoga Playlist Creator", page_icon="🧘‍♀️", layout="wide")
    
    st.markdown("""
        <style>
        .stAlert {border-radius: 10px;}
        .stProgress .st-bp {background-color: #9DB5B2;}
        div[data-testid="stExpander"] {border-radius: 10px; border: 1px solid #ddd;}
        .song-link {
            display: inline-block;
            padding: 2px 8px;
            margin: 2px;
            border-radius: 4px;
            text-decoration: none;
            font-size: 12px;
        }
        .spotify-link {
            background-color: #1DB954;
            color: white !important;
        }
        .youtube-link {
            background-color: #FF0000;
            color: white !important;
        }
        </style>
    """, unsafe_allow_html=True)
    
    st.title("🧘‍♀️ Yoga Playlist Recommender")
    
    if 'recommendations' not in st.session_state:
        st.session_state.recommendations = None
    if 'playlist_history' not in st.session_state:
        st.session_state.playlist_history = []
    
    with st.sidebar:
        st.header("🎵 Recent Playlists")
        for idx, playlist in enumerate(st.session_state.playlist_history[-5:]):
            st.text(f"{idx + 1}. {playlist['theme']}")
    
    col1, col2 = st.columns([2, 1])
    
    with col1:
        theme = st.text_input("Enter your desired music theme:", 
                            placeholder="e.g., lo-fi, calm edm, country, rap")
        
        preferences = st.text_area("Additional preferences (optional):",
                                placeholder="e.g., female vocals, instrumental only, specific artists...")
        
        class_duration = st.selectbox("Class Duration:", 
                                    options=["45", "60", "75"],
                                    index=1,
                                    format_func=lambda x: f"{x} Minutes")
        
        col1_1, col1_2 = st.columns(2)
        with col1_1:
            generate = st.button("🎵 Generate Playlist", type="primary", use_container_width=True)
        with col1_2:
            clear = st.button("🗑️ Clear", type="secondary", use_container_width=True)
            if clear:
                st.session_state.recommendations = None
    
    if generate:
        if not theme:
            st.error("Please enter a music theme.")
        else:
            with st.spinner("Creating your perfect yoga playlist..."):
                st.session_state.recommendations = get_claude_recommendations(
                    f"{theme} {preferences}".strip(),
                    class_duration
                )
                if st.session_state.recommendations:
                    st.session_state.playlist_history.append({
                        'theme': theme,
                        'duration': f"{class_duration} minutes",
                        'timestamp': datetime.now(),
                        'recommendations': st.session_state.recommendations
                    })
    
    if st.session_state.recommendations:
        st.markdown(f"### 🎵 Your {class_duration}-Minute Yoga Playlist")
        
        total_duration = 0
        for section, details in st.session_state.recommendations['sections'].items():
            with st.expander(f"🎼 {section} ({details['duration']} | Intensity: {details['section_intensity']})"):
                # Create DataFrame with all columns except URLs
                display_df = pd.DataFrame([{k: v for k, v in song.items() 
                                          if k not in ['spotify_url', 'youtube_url']} 
                                         for song in details['songs']])
                
                st.dataframe(
                    display_df,
                    hide_index=True,
                    column_config={
                        "name": st.column_config.TextColumn("Song"),
                        "artist": st.column_config.TextColumn("Artist"),
                        "length": st.column_config.TextColumn("Duration"),
                        "intensity": st.column_config.NumberColumn(
                            "Intensity",
                            help="1 (very calm) to 5 (high energy)",
                            min_value=1,
                            max_value=5,
                            format="%d ⚡"
                        ),
                        "reason": st.column_config.TextColumn("Why This Song")
                    }
                )
                
                # Display music platform links
                for song in details['songs']:
                    st.markdown(f"""
                        **{song['name']}** - Listen on: 
                        <a href="{song['spotify_url']}" target="_blank" class="song-link spotify-link">Spotify</a> 
                        <a href="{song['youtube_url']}" target="_blank" class="song-link youtube-link">YouTube</a>
                    """, unsafe_allow_html=True)
                
                section_duration = sum(calculate_duration(song['length']) for song in details['songs'])
                total_duration += section_duration
                st.caption(f"Section duration: {section_duration//60}:{section_duration%60:02d}")
        
        st.success(f"Total Playlist Duration: {total_duration//60} minutes {total_duration%60} seconds")
        
        col3, col4 = st.columns(2)
        with col3:
            st.download_button(
                "💾 Download Playlist",
                data=json.dumps(st.session_state.recommendations, indent=4),
                file_name=f"yoga_playlist_{theme}_{class_duration}min_{datetime.now().strftime('%Y%m%d_%H%M')}.json",
                mime="application/json",
                use_container_width=True
            )

if __name__ == "__main__":
    main()
