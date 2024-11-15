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
    
    prompt = f"""Create a yoga playlist for a {class_duration}-minute class with theme: {theme}. Return ONLY a JSON object like this example (replace example values with real songs that match the theme):

{{
  "sections": {{
    "Grounding & Warm Up": {{
      "duration": "{section_times['Grounding & Warm Up']} minutes",
      "section_intensity": "1-2",
      "songs": [
        {{
          "name": "Example Song",
          "artist": "Example Artist",
          "length": "03:30",
          "intensity": 1,
          "reason": "Brief reason",
          "spotify_url": "https://open.spotify.com/track/example",
          "youtube_url": "https://youtube.com/watch?v=example"
        }}
      ]
    }},
    "Sun Salutations": {{
      "duration": "{section_times['Sun Salutations']} minutes",
      "section_intensity": "2-3",
      "songs": [
        {{
          "name": "Example Song",
          "artist": "Example Artist",
          "length": "03:30",
          "intensity": 2,
          "reason": "Brief reason",
          "spotify_url": "https://open.spotify.com/track/example",
          "youtube_url": "https://youtube.com/watch?v=example"
        }}
      ]
    }},
    "Movement Series 1": {{
      "duration": "{section_times['Movement Series 1']} minutes",
      "section_intensity": "2-3",
      "songs": [
        {{
          "name": "Example Song",
          "artist": "Example Artist",
          "length": "03:30",
          "intensity": 2,
          "reason": "Brief reason",
          "spotify_url": "https://open.spotify.com/track/example",
          "youtube_url": "https://youtube.com/watch?v=example"
        }}
      ]
    }},
    "Movement Series 2": {{
      "duration": "{section_times['Movement Series 2']} minutes",
      "section_intensity": "3-4",
      "songs": [
        {{
          "name": "Example Song",
          "artist": "Example Artist",
          "length": "03:30",
          "intensity": 3,
          "reason": "Brief reason",
          "spotify_url": "https://open.spotify.com/track/example",
          "youtube_url": "https://youtube.com/watch?v=example"
        }}
      ]
    }},
    "Integration Series": {{
      "duration": "{section_times['Integration Series']} minutes",
      "section_intensity": "2-3",
      "songs": [
        {{
          "name": "Example Song",
          "artist": "Example Artist",
          "length": "03:30",
          "intensity": 2,
          "reason": "Brief reason",
          "spotify_url": "https://open.spotify.com/track/example",
          "youtube_url": "https://youtube.com/watch?v=example"
        }}
      ]
    }},
    "Savasana": {{
      "duration": "{section_times['Savasana']} minutes",
      "section_intensity": "1-2",
      "songs": [
        {{
          "name": "Example Song",
          "artist": "Example Artist",
          "length": "03:30",
          "intensity": 1,
          "reason": "Brief reason",
          "spotify_url": "https://open.spotify.com/track/example",
          "youtube_url": "https://youtube.com/watch?v=example"
        }}
      ]
    }}
  }}
}}

Requirements:
1. Include 2-3 songs per section that fit the time limit
2. Each song should have working Spotify and YouTube links
3. Song intensity should match section_intensity
4. Use MM:SS format for length
5. Keep reasons brief and relevant"""

    try:
        message = anthropic_client.beta.messages.create(
            model="claude-3-sonnet-20240229",
            max_tokens=1500,
            temperature=0.7,
            system="You are a yoga music expert. Return ONLY valid JSON with no additional text.",
            messages=[{"role": "user", "content": prompt}]
        )
        
        # Clean and parse JSON
        response_text = message.content[0].text.strip()
        
        # Remove any potential markdown code block markers
        response_text = response_text.replace('```json', '').replace('```', '').strip()
        
        # Find the actual JSON content
        json_start = response_text.find('{')
        json_end = response_text.rfind('}') + 1
        if json_start >= 0 and json_end > json_start:
            json_str = response_text[json_start:json_end]
            try:
                parsed_json = json.loads(json_str)
                return parsed_json
            except json.JSONDecodeError as e:
                st.error(f"Invalid JSON structure: {str(e)}")
                st.error("Please try again - the AI sometimes returns malformed responses")
                return None
        else:
            st.error("Could not find valid JSON in the response")
            return None
            
    except Exception as e:
        st.error(f"Error getting recommendations: {str(e)}")
        st.error("Please try again - the AI sometimes needs multiple attempts")
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
            padding: 4px 12px;
            margin: 2px 4px;
            border-radius: 20px;
            text-decoration: none;
            font-size: 12px;
            font-weight: 500;
            transition: opacity 0.2s;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        }
        .song-link:hover {
            opacity: 0.9;
            box-shadow: 0 4px 8px rgba(0,0,0,0.2);
        }
        .spotify-link {
            background-color: #1DB954;
            color: white !important;
        }
        .youtube-link {
            background-color: #FF0000;
            color: white !important;
        }
        .song-title {
            font-weight: 500;
            margin-top: 10px;
            margin-bottom: 4px;
            padding: 4px 8px;
            background-color: #f8f9fa;
            border-radius: 4px;
        }
        .song-links {
            margin-bottom: 12px;
            padding-left: 8px;
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
        for idx, playlist in enumerate(reversed(st.session_state.playlist_history[-5:])):
            with st.expander(f"🎵 {playlist['theme']} ({playlist['duration']})"):
                st.text(f"Created: {playlist['timestamp'].strftime('%Y-%m-%d %H:%M')}")
    
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
                        <div class="song-title">{song['name']} by {song['artist']}</div>
                        <div class="song-links">
                            <a href="{song['spotify_url']}" target="_blank" class="song-link spotify-link">
                                ▶️ Listen on Spotify
                            </a>
                            <a href="{song['youtube_url']}" target="_blank" class="song-link youtube-link">
                                ▶️ Watch on YouTube
                            </a>
                        </div>
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
