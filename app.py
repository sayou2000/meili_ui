```python
import os
import streamlit as st
from meilisearch import Client
import requests

# --- Konfiguration aus Umgebungsvariablen ---
MEILI_URL = os.getenv("MEILI_URL")
MEILI_API_KEY = os.getenv("MEILI_API_KEY")
MEILI_INDEX = os.getenv("MEILI_INDEX", "testdokumente")
OPENAI_URL = "https://api.openai.com/v1/chat/completions"
OPENAI_KEY = os.getenv("OPENAI_API_KEY")
OPENAI_MODEL = os.getenv("OPENAI_MODEL", "o4-mini-2025-04-16")

# Validierung der Schlüssel
if not MEILI_URL or not MEILI_API_KEY:
    st.error("Fehler: Meilisearch-Zugangsdaten fehlen. Bitte MEILI_URL und MEILI_API_KEY setzen.")
    st.stop()
if not OPENAI_KEY:
    st.error("Fehler: OpenAI-API-Schlüssel fehlt. Bitte OPENAI_API_KEY setzen.")
    st.stop()

# --- Meilisearch-Client (gecached) ---
@st.cache_resource
def init_meili_index(url: str, key: str, index_name: str):
    client = Client(url, key)
    return client.index(index_name)

index = init_meili_index(MEILI_URL, MEILI_API_KEY, MEILI_INDEX)

# --- Streamlit UI ---
st.set_page_config(page_title="🔎 Intelligente Dokumentensuche", layout="wide")
st.title("🔎 Intelligente Dokumentensuche")

# Sucheingabe als Formular
with st.form(key="search_form"):
    query = st.text_input("Suchanfrage", placeholder="z.B. SAP Instandhaltung")
    submit = st.form_submit_button("🔍 Suchen")

if submit and query:
    with st.spinner("Suche in Meilisearch läuft..."):
        try:
            params = {
                "limit": 10,
                "attributesToHighlight": ["content"],
                "attributesToSnippet": ["content:200"],
                "highlightPreTag": "<mark style='background-color:yellow'>",
                "highlightPostTag": "</mark>",
            }
            response = index.search(query, params)
            hits = response.get("hits", [])
        except Exception as err:
            st.error(f"Meilisearch-Fehler: {err}")
            hits = []

    if not hits:
        st.warning("Keine Treffer gefunden."
                   " Versuchen Sie eine andere Suchanfrage.")
    else:
        st.subheader(f"{len(hits)} Treffer für '{query}':")
        for hit in hits:
            filename = hit.get("filename", hit.get("id", "Dokument"))
            snippet = hit.get("_formatted", {}).get("content", "")

            with st.expander(filename):
                st.markdown(snippet, unsafe_allow_html=True)

                # KI-Analyse
                btn_key = f"ai_{hit.get('id')}"
                if st.button("🧠 Kontext-KI-Analyse", key=btn_key):
                    with st.spinner("KI-Analyse läuft..."):
                        # Markierungen entfernen
                        clean = snippet.replace("<mark style='background-color:yellow'>", "")
                        clean = clean.replace("</mark>", "")
                        prompt = (
                            f"Du bist ein Experte für Dokumentenanalyse."
                            f"\nNutzerfrage: '{query}'\n\n"
                            f"Relevante Textausschnitte:\n{clean}\n\n"
                            f"Bitte beantworte **ausschließlich** auf Basis dieses Textes und verweise auf die Stellen."
                        )
                        headers = {
                            "Authorization": f"Bearer {OPENAI_KEY}",
                            "Content-Type": "application/json"
                        }
                        body = {
                            "model": OPENAI_MODEL,
                            "messages": [{"role": "user", "content": prompt}],
                            "temperature": 0.2
                        }
                        try:
                            r = requests.post(OPENAI_URL, headers=headers, json=body, timeout=20)
                            r.raise_for_status()
                            answer = r.json()["choices"][0]["message"]["content"]
                            st.success(answer)
                        except requests.RequestException as e:
                            st.error(f"OpenAI-Fehler: {e}")

# --- Sidebar ---
st.sidebar.header("ℹ️ Info und Sicherheit")
st.sidebar.markdown(
    """
    - **Meilisearch URL** und **Key** bitte als Umgebungsvariablen setzen.
    - **OpenAI-API-Key** niemals im Code ablegen, sondern als Secret konfigurieren.
    - Secrets in Streamlit Cloud unter "Manage App > Secrets" hinzufügen.
    """
)
st.sidebar.markdown(f"**Index:** `{MEILI_INDEX}`")
st.sidebar.markdown(f"**KI-Modell:** `{OPENAI_MODEL}`")
```
