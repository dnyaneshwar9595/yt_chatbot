import streamlit as st
import streamlit.components.v1 as components
from openai import OpenAI
from helpers import get_youtube_id, fetch_transcript
from dotenv import load_dotenv
load_dotenv()
# --- LLM setup ---
client = OpenAI()  # uses OPENAI_API_KEY from env

st.set_page_config(page_title="AI Video Assistant", layout="wide")

# --- Session state ---
if "chat_history" not in st.session_state:
    st.session_state.chat_history = []
if "context" not in st.session_state:
    st.session_state.context = ""

# --- Sidebar for video input ---
st.sidebar.title("🎥 Video Settings")
video_url = st.sidebar.text_input("Enter YouTube URL:")
load_btn = st.sidebar.button("Load Video")

if load_btn and video_url:
    try:
        video_id = get_youtube_id(video_url)
        st.session_state.context = fetch_transcript(video_id)
        st.sidebar.success("Video loaded successfully ✅")
        st.session_state.chat_history = []  # reset chat when new video loads
        st.session_state.video_id = video_id
    except Exception as e:
        st.sidebar.error(f"Could not fetch video: {e}")

# --- Layout ---
st.title("🤖 AI Video Assistant")

# Left: video | Right: chat
col1, col2 = st.columns([1.2, 1.3])

# ---------- LEFT COLUMN (Video) ----------
with col1:
    if "video_id" in st.session_state:
        video_id = st.session_state.video_id
        components.html(
            f"""
            <div style="position:relative;padding-bottom:56.25%;height:0;overflow:hidden;border-radius:12px;">
                <iframe src="https://www.youtube.com/embed/{video_id}"
                        frameborder="0" allowfullscreen
                        style="position:absolute;top:0;left:0;width:100%;height:100%;">
                </iframe>
            </div>
            """,
            height=450,
        )
    else:
        st.info("Paste a YouTube link in the sidebar to start ▶️")

# ---------- RIGHT COLUMN (Chat) ----------
with col2:
    st.subheader("💬 Ask about the video")

    # Display chat history
    for msg in st.session_state.chat_history:
        with st.chat_message(msg["role"]):
            st.markdown(msg["content"])

    # Chat input
    user_input = st.chat_input("Ask your question...")
    if user_input and st.session_state.context:
        # Append user message
        st.session_state.chat_history.append({"role": "user", "content": user_input})

        with st.chat_message("assistant"):
            message_placeholder = st.empty()
            full_response = ""

            # --- Streaming LLM response ---
            stream = client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {"role": "system", "content": "You are a helpful assistant answering questions about a video transcript."},
                    {"role": "user", "content": f"Transcript:\n{st.session_state.context}"},
                    {"role": "user", "content": user_input},
                ],
                stream=True,
            )

            for chunk in stream:
                if chunk.choices[0].delta.content:
                    full_response += chunk.choices[0].delta.content
                    message_placeholder.markdown(full_response + "▌")
            message_placeholder.markdown(full_response)

        st.session_state.chat_history.append({"role": "assistant", "content": full_response})
