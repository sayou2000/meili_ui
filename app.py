import os
import streamlit as st
from meilisearch import Client
import requests

# Optionales Laden von .env, wenn dotenv installiert ist
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

# --- Konfiguration ---
# Umgebungsvariablen sicher laden
MEILI_URL = os.getenv("MEILI_URL")
MEILI_API_KEY = os.getenv("MEILI_API_KEY")
INDEX_NAME = os.getenv("MEILI_INDEX", "testdokumente")
OPENAI_URL = "https://api.openai.com/v1/chat/completions"
OPENAI_KEY = os.getenv("OPENAI_API_KEY")
MODEL = os.getenv("OPENAI_MODEL", "gpt-4o-mini") # Aktualisiert auf ein häufigeres Modell

# --- Initialisierung (gecached) ---
@st.cache_resource
def get_meilisearch_client():
    """Initialisiert den Meilisearch-Client und hält ihn im Cache."""
    if not MEILI_URL or not MEILI_API_KEY:
        st.error("Meilisearch URL oder API Key nicht konfiguriert! Bitte als Umgebungsvariable setzen.")
        return None
    client = Client(MEILI_URL, MEILI_API_KEY)
    return client.index(INDEX_NAME)

index = get_meilisearch_client()

# --- Streamlit UI ---
st.set_page_config(page_title="🔎 Intelligente Dokumentensuche", layout="wide")
st.title("🔎 Intelligente Dokumentensuche")

# Initialisiere Session State, falls noch nicht vorhanden
if 'search_results' not in st.session_state:
    st.session_state.search_results = None

# Sucheingabe-Formular für bessere Kontrolle
with st.form(key='search_form'):
    query = st.text_input("Was möchten Sie wissen oder finden?", key="search_input")
    submit_button = st.form_submit_button(label='Suchen')

# Logik für die Suche
if submit_button and query and index:
    with st.spinner("Suche läuft..."):
        try:
            # Suchparameter als Dictionary definieren
            search_params = {
                "limit": 10,
                "attributesToHighlight": ["content"],
                "attributesToSnippet": ["content:200"],
                "highlightPreTag": "<mark style='background-color:yellow'>",
                "highlightPostTag": "</mark>",
            }
            # KORREKTUR: Das Dictionary direkt übergeben, nicht entpacken
            response = index.search(query, search_params)
            st.session_state.search_results = response.get("hits", [])
        except Exception as e:
            st.error(f"Fehler bei der Meilisearch-Suche: {e}")
            st.session_state.search_results = [] # Fehlerfall behandeln

# Ergebnisse anzeigen, wenn vorhanden
if st.session_state.search_results is not None:
    results = st.session_state.search_results
    if not results:
        st.warning("Keine Treffer für Ihre Anfrage gefunden.")
    else:
        st.subheader(f"{len(results)} Treffer gefunden:")
        for i, hit in enumerate(results):
            # Verwendung eines Expanders für eine saubere Darstellung
            with st.expander(f"**Dokument: {hit.get('filename', f'Treffer {i+1}')}**"):
                # Formatierten Inhalt anzeigen
                st.markdown(
                    hit.get("_formatted", {}).get("content", "Kein Vorschau-Inhalt verfügbar."),
                    unsafe_allow_html=True
                )

                # KI-Analyse Button
                analyze_key = f"analyze_{hit.get('id', i)}"
                if st.button("🧠 Kontextbezogene KI-Analyse durchführen", key=analyze_key):
                    with st.spinner("Dokument wird mit KI analysiert..."):
                        snippet = hit.get("_formatted", {}).get("content", "")
                        # Markierungen für den Prompt entfernen
                        clean_snippet = snippet.replace("<mark style='background-color:yellow'>", "").replace("</mark>", "")
                        
                        prompt = (
                            f"Du bist ein hilfreicher Assistent für Dokumentenanalyse.\n"
                            f"Beantworte die folgende Nutzerfrage präzise und ausschließlich basierend auf dem bereitgestellten Textausschnitt.\n\n"
                            f"Nutzerfrage: \"{query}\"\n\n"
                            f"Relevanter Textausschnitt aus dem Dokument '{hit.get('filename', 'unbekannt')}':\n---\n{clean_snippet}\n---\n\n"
                            f"Deine Antwort:"
                        )
                        
                        headers = {"Authorization": f"Bearer {OPENAI_KEY}", "Content-Type": "application/json"}
                        payload = {"model": MODEL, "messages": [{"role": "user", "content": prompt}], "temperature": 0.2}
                        
                        try:
                            resp = requests.post(OPENAI_URL, headers=headers, json=payload, timeout=30)
                            resp.raise_for_status() # Löst einen Fehler bei 4xx oder 5xx Antworten aus
                            
                            ai_answer = resp.json()["choices"][0]["message"]["content"]
                            st.info(f"**KI-Analyse:**\n{ai_answer}")

                        except requests.exceptions.RequestException as e:
                            st.error(f"Fehler bei der Verbindung zur KI-API: {e}")
                        except Exception as e:
                            st.error(f"Ein unerwarteter Fehler bei der KI-Analyse ist aufgetreten: {e}")

# --- Sidebar ---
st.sidebar.header("ℹ️ Info")
st.sidebar.markdown(
    """
    Diese App durchsucht einen Meilisearch-Index und ermöglicht eine kontextbezogene Analyse der Suchergebnisse mittels einer KI.

    **Verwendung:**
    1. Suchanfrage eingeben und auf "Suchen" klicken.
    2. Die gefundenen Dokumente werden unten aufgelistet.
    3. Klappen Sie ein Dokument auf, um die Details zu sehen.
    4. Klicken Sie auf "KI-Analyse", um die KI die Relevanz des Textes für Ihre Frage bewerten zu lassen.
    """
)
st.sidebar.markdown("---")
st.sidebar.markdown(f"**Meilisearch Index:** `{INDEX_NAME}`")
st.sidebar.markdown(f"**KI Modell:** `{MODEL}`")
