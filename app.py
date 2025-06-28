import os
import streamlit as st
from meilisearch import Client
import requests
from dotenv import load_dotenv

# Laden der Umgebungsvariablen
load_dotenv()
MEILI_URL = os.getenv("MEILI_URL")
MEILI_API_KEY = os.getenv("MEILI_API_KEY")
INDEX_NAME = os.getenv("MEILI_INDEX", "testdokumente")
OPENAI_URL = "https://api.openai.com/v1/chat/completions"
OPENAI_KEY = os.getenv("OPENAI_API_KEY")
MODEL = os.getenv("OPENAI_MODEL", "o4-mini-2025-04-16")

# Meilisearch-Client initialisieren
client = Client(MEILI_URL, MEILI_API_KEY)
index = client.index(INDEX_NAME)

st.set_page_config(page_title="🔎 Intelligente Dokumentensuche", layout="wide")
st.title("🔎 Intelligente Dokumentensuche")

# Sucheingabe
query = st.text_input("Was möchten Sie wissen oder finden?", "", key="search_input")
if st.button("Suchen") and query:
    with st.spinner("Suche läuft..."):
        try:
            search_params = {
                "q": query,
                "limit": 10,
                "attributesToHighlight": ["content"],
                "attributesToSnippet": ["content:200"],
                "highlightPreTag": "<mark style='background-color:yellow'>",
                "highlightPostTag": "</mark>",
            }
            results = index.search(**search_params)["hits"]
            if not results:
                st.warning("Keine Treffer gefunden.")
            else:
                for hit in results:
                    st.subheader(hit.get("filename", "Unbekanntes Dokument"))
                    st.markdown(hit.get("_formatted", {}).get("content", ""), unsafe_allow_html=True)
                    # KI-Analyse Button pro Dokument
                    if st.button(f"KI-Analyse: {hit['id']}"):
                        with st.spinner("Analysiere mit KI..."):
                            snippet = hit.get("_formatted", {}).get("content", "")
                            clean_snippet = snippet.replace("<mark style='background-color:yellow'>", "").replace("</mark>", "")
                            prompt = (
                                f"Du bist ein Experte für Dokumentenanalyse.\n"
                                f"Nutzerfrage: \"{query}\"\n\n"
                                f"Relevante Textausschnitte:\n{clean_snippet}\n\n"
                                f"Bitte beantworte die Frage basierend auf diesen Ausschnitten, und verweise auf die Stellen."
                            )
                            headers = {
                                "Authorization": f"Bearer {OPENAI_KEY}",
                                "Content-Type": "application/json"
                            }
                            payload = {
                                "model": MODEL,
                                "messages": [{"role": "user", "content": prompt}]
                            }
                            resp = requests.post(OPENAI_URL, headers=headers, json=payload)
                            if resp.ok:
                                ai_answer = resp.json()["choices"][0]["message"]["content"]
                                st.markdown(f"**🧠 KI-Analyse:** {ai_answer}")
                            else:
                                st.error(f"Fehler bei OpenAI: {resp.text}")
        except Exception as e:
            st.error(f"Fehler bei der Suche: {e}")

# Footer Info
st.sidebar.header("ℹ️ Verwendung")
st.sidebar.markdown(
    """
- Geben Sie Ihre Suchanfrage ein und klicken Sie auf "Suchen".
- Die gefundenen Stellen werden hervorgehoben angezeigt.
- Führen Sie pro Dokument eine KI-Analyse durch.
- Konfigurieren Sie Ihre API-Keys über Umgebungsvariablen.
"""
)
