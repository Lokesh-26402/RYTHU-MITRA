# --- AGRI-TOOL: Full UI Revamp ---
import streamlit as st
from PIL import Image
import io
import speech_recognition as sr
import google.generativeai as genai
import requests
from gtts import gTTS
import tempfile
import datetime
import geocoder
import unicodedata

# --- Configure Gemini API ---
genai.configure(api_key="AIzaSyADAFye4AdI16sPJoxIx9KtnuZQTg3dmwI")
model = genai.GenerativeModel("gemini-2.5-flash")

# --- Configure WeatherAPI ---
WEATHERAPI_KEY = "2385b7a7051045f382d62111252807"

# --- Page Config ---
st.set_page_config(page_title="🌾 AGRI-TOOL", layout="wide")

# --- Inject Enhanced CSS ---
st.markdown("""
<style>
body {
    background: linear-gradient(-45deg, #e3f2fd, #f1f8e9, #ffe0b2, #e1bee7);
    background-size: 400% 400%;
    animation: gradientBG 15s ease infinite;
    font-family: 'Segoe UI', sans-serif;
}

@keyframes gradientBG {
  0% {background-position: 0% 50%;}
  50% {background-position: 100% 50%;}
  100% {background-position: 0% 50%;}
}

section[data-testid="stSidebar"] {
    background-color: #e8f5e9;
    border-right: 2px solid #81c784;
}

h1, h2, h3, .stTextInput label, .stSlider label, .stNumberInput label {
    color: #2e7d32 !important;
    transition: color 0.3s;
}

.stButton>button {
    background-color: #43a047;
    color: white;
    font-weight: bold;
    border-radius: 10px;
    transition: all 0.3s ease-in-out;
    box-shadow: 0px 4px 8px rgba(67, 160, 71, 0.3);
}
.stButton>button:hover {
    background-color: #2e7d32;
    transform: scale(1.05);
    box-shadow: 0px 6px 12px rgba(46, 125, 50, 0.4);
}

.stRadio>div {
    background-color: #f0f4c3;
    padding: 0.5rem;
    border-radius: 12px;
    transition: background-color 0.3s, transform 0.2s;
}
.stRadio>div:hover {
    background-color: #dce775;
    transform: scale(1.01);
}

.st-expander {
    border: 1.5px solid #aed581 !important;
    border-radius: 12px !important;
    background-color: #f9fbe7 !important;
    transition: all 0.3s ease-in-out;
}
.st-expander:hover {
    box-shadow: 0px 4px 12px rgba(173, 209, 88, 0.2);
}
</style>
""", unsafe_allow_html=True)

# --- Title and Language ---
st.title("🌾 AGRI-TOOL – AI Assistant for Farmers")
st.markdown("Empowering Farmers with AI 🌾 Weather, Crops, Diseases & More!")

lang = st.sidebar.selectbox("🌐 Select Language", ["English", "Telugu", "Hindi"])
lang_map = {
    "English": "Respond in English.",
    "Telugu": "స్పష్టంగా తెలుగులో స్పందించండి.",
    "Hindi": "कृपया स्पष्ट हिंदी में उत्तर दीजिए।"
}


# --- Utility Functions ---
def get_gtts_lang_code(lang):
    return {"English": "en", "Telugu": "te", "Hindi": "hi"}.get(lang, "en")


def speak(text):
    try:
        tts = gTTS(text=text, lang=get_gtts_lang_code(lang))
        with tempfile.NamedTemporaryFile(delete=False, suffix=".mp3") as fp:
            tts.save(fp.name)
            st.audio(fp.name, format="audio/mp3", autoplay=True)
    except:
        st.warning("🔈 Failed to play audio.")


def recognize_speech():
    r = sr.Recognizer()
    with sr.Microphone() as source:
        st.info("🎤 Listening (6s max)...")
        try:
            audio = r.listen(source, timeout=3, phrase_time_limit=6)
            query = r.recognize_google(audio)
            st.success(f"🗣 You said: {query}")
            return query
        except sr.WaitTimeoutError:
            st.warning("⏱ No voice detected in time.")
        except:
            st.error("❌ Could not recognize speech.")
    return None


def gemini_text_response(user_input, system_prompt, lang_instruction):
    prompt = f"{system_prompt}\n\n{lang_instruction}\n\nUser: {user_input}"
    return model.generate_content(prompt).text


def gemini_image_analysis(image_bytes):
    prompt = (
        "Analyze this image and identify crop disease, pest, or soil issue. "
        "Suggest treatment including pesticides, fertilizers, and best practices. "
        f"{lang_map[lang]}"
    )
    return model.generate_content([
        {"mime_type": "image/jpeg", "data": image_bytes},
        prompt
    ]).text


def get_weather_advisory(location):
    try:
        url = f"http://api.weatherapi.com/v1/current.json?key={WEATHERAPI_KEY}&q={location}&aqi=no"
        data = requests.get(url).json()
        if "error" in data:
            return "❌ Location not found or weather service error."
        info = data["current"]
        name = data["location"]["name"]
        advisory_text = f"""
📍 *Weather in {name}*:
- 🌡 Temperature: {info['temp_c']}°C
- 🌫 Condition: {info['condition']['text']}
- 💧 Humidity: {info['humidity']}%
- 🌬 Wind: {info['wind_kph']} km/h
- ☔ Rainfall: {info.get('precip_mm', 0)} mm

📢 *Advice*:
- {'Delay irrigation.' if info.get('precip_mm', 0) > 2 else 'Consider irrigation.'}
- Monitor for fungal infections in humidity.
        """
        return gemini_text_response(advisory_text, "Summarize the weather advisory:", lang_map[lang])
    except Exception as e:
        return f"⚠ Error fetching weather data: {e}"


def get_user_location():
    try:
        g = geocoder.ip('me')
        city = g.city or g.address or ""
        if city:
            city = unicodedata.normalize('NFKD', city).encode('ascii', 'ignore').decode('utf-8')
            return city.strip()
        return ""
    except:
        return ""


# --- Sidebar ---
option = st.sidebar.radio("📋 Services", [
    "🌿 Crop & Disease Detection",
    "🤖 AI Farming Chatbot",
    "☔ Weather Advisory",
    "🧪 Soil & Fertilizer Advice",
    "🏫 Govt. Schemes",
    "🖖 Crop Calendar",
    "👨‍🌾 Contact Agri Officer"
])

user_location = get_user_location()

# --- Main Features ---
if option == "🌿 Crop & Disease Detection":
    st.header("🌿 Detect Crop Issues from Image")
    source = st.radio("Image Source", ["📷 Camera", "📁 Upload"], horizontal=True)
    image = st.camera_input("Take photo") if source == "📷 Camera" else st.file_uploader("Upload image", type=["jpg", "jpeg", "png"])
    if image:
        img = Image.open(image)
        st.image(img, use_container_width=True)
        buf = io.BytesIO()
        img.save(buf, format='JPEG')
        result = gemini_image_analysis(buf.getvalue())
        with st.expander("📄 Analysis Result"):
            st.write(result)
        speak(result)

elif option == "🤖 AI Farming Chatbot":
    st.header("🤖 Ask AI your farming doubts")
    query = st.text_input("Type your question")
    if st.button("🎤 Speak"):
        query = recognize_speech()
    if query:
        result = gemini_text_response(query, "You are an intelligent farming assistant.", lang_map[lang])
        with st.expander("💬 Response"):
            st.write(result)
        speak(result)

if option == "☔ Weather Advisory":
    st.header("☔ Weather Advisory")
    location = user_location or st.text_input("📍 Enter your location:")
    if location:
        response = get_weather_advisory(location)
        st.markdown(response)
        speak(response)

elif option == "🧪 Soil & Fertilizer Advice":
    st.header("🧪 Enter Soil Values")
    ph = st.slider("🌡 Soil pH", 3.5, 9.0, 6.5)
    n = st.number_input("🌱 Nitrogen (ppm)", 0, 1000, 50)
    p = st.number_input("🌾 Phosphorus (ppm)", 0, 1000, 30)
    k = st.number_input("🍠 Potassium (ppm)", 0, 1000, 40)
    if st.button("🧮 Analyze"):
        prompt = f"Soil has pH {ph}, N={n}, P={p}, K={k}. Suggest fertilizer plan including organic options."
        result = gemini_text_response(prompt, "You are a soil nutrition expert.", lang_map[lang])
        with st.expander("🧫 Recommendation"):
            st.write(result)
        speak(result)

elif option == "🏫 Govt. Schemes":
    st.header("🏫 Government Scheme Lookup")
    scheme = st.text_input("Enter keyword or crop")
    if st.button("🎤 Speak"):
        scheme = recognize_speech()
    if scheme:
        result = gemini_text_response(scheme, "You help farmers find schemes.", lang_map[lang])
        with st.expander("🏛 Schemes"):
            st.write(result)
        speak(result)



if option == "🖖 Crop Calendar":
    st.header("🖖 Crop Calendar")
    month = st.selectbox("📅 Select Month", [datetime.datetime(2000, m, 1).strftime('%B') for m in range(1, 13)], index=datetime.datetime.now().month - 1)
    prompt = f"I am a farmer in {user_location or 'India'}. What crops should I grow in {month}?"
    response = gemini_text_response("", prompt, lang_map[lang])
    st.markdown(response)
    speak(response)


elif option == "👨‍🌾 Contact Agri Officer":
    st.header("👨‍🌾 Find Agriculture Contacts")
    loc = st.text_input("📍 Location:", user_location)
    if st.button("🎤 Speak"):
        loc = recognize_speech()
    if loc:
        prompt = f"Contact info for agriculture officer, KVKs, helplines in {loc}. {lang_map[lang]}"
        result = gemini_text_response(prompt, "You are an agriculture contact assistant.", lang_map[lang])
        with st.expander("📞 Contacts"):
            st.write(result)
        speak(result)

# --- Footer ---
st.markdown("---")
st.caption(f"🌐 Language: {lang} | Gemini AI + WeatherAPI | Made for Indian Farmers 🇮🇳")