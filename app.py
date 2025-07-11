import os
import streamlit as st
from meilisearch import Client
import requests

# --- Konfiguration über Streamlit Secrets ---
MEILI_URL = st.secrets.get("MEILI_URL")
MEILI_API_KEY = st.secrets.get("MEILI_API_KEY")
MEILI_INDEX = st.secrets.get("MEILI_INDEX", "testdokumente")
OPENAI_KEY = st.secrets.get("OPENAI_API_KEY")
OPENAI_MODEL = st.secrets.get("OPENAI_MODEL", "o4-mini-2025-04-16")
OPENAI_URL = "https://api.openai.com/v1/chat/completions"

# Validierung der Schlüssel
if not MEILI_URL or not MEILI_API_KEY:
    st.error("Fehler: Meilisearch-Zugangsdaten fehlen. Bitte unter Secrets setzen: MEILI_URL & MEILI_API_KEY.")
    st.stop()
if not OPENAI_KEY:
    st.error("Fehler: OpenAI-API-Schlüssel fehlt. Bitte unter Secrets setzen: OPENAI_API_KEY.")
    st.stop()

# --- Meilisearch-Client (gecached) ---
@st.cache_resource
def init_meili_index():
    client = Client(MEILI_URL, MEILI_API_KEY)
    return client.index(MEILI_INDEX)

index = init_meili_index()

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
            response = index.search(query, {
                "limit": 10,
                "attributesToHighlight": ["content"],
                "highlightPreTag": "<mark style='background-color:yellow'>",
                "highlightPostTag": "</mark>"
            })
            hits = response.get("hits", [])
        except Exception as err:
            st.error(f"Meilisearch-Fehler: {err}")
            hits = []

    if not hits:
        st.warning("Keine Treffer gefunden. Versuchen Sie eine andere Suchanfrage.")
    else:
        st.subheader(f"{len(hits)} Treffer für '{query}':")

        all_snippets = []
        for hit in hits:
            filename = hit.get("filename", hit.get("id", "Dokument"))
            snippet = hit.get("_formatted", {}).get("content", "")
            clean = snippet.replace("<mark style='background-color:yellow'>", "").replace("</mark>", "")
            all_snippets.append(f"Dokument: {filename}\n---\n{clean}\n")

            with st.expander(filename):
                st.markdown(snippet, unsafe_allow_html=True)

        # Gesamte KI-Analyse auf alle Snippets
        if st.button("🧠 KI-Zusammenfassung aller Fundstellen"):
            with st.spinner("KI analysiert mehrere Fundstellen..."):
                full_context = "\n\n".join(all_snippets)
                prompt = (
                    f"Du bist ein Experte für Dokumentenanalyse.\n"
                    f"Nutzerfrage: '{query}'\n\n"
                    f"Hier sind relevante Textauszüge aus verschiedenen Dokumenten:\n---\n{full_context}\n---\n\n"
                    f"Bitte beantworte die Frage basierend auf diesen Auszügen so prägnant und fundiert wie möglich."
                )
                headers = {"Authorization": f"Bearer {OPENAI_KEY}", "Content-Type": "application/json"}
                body = {"model": OPENAI_MODEL, "messages": [{"role": "user", "content": prompt}], "temperature": 0.2}
                try:
                    r = requests.post(OPENAI_URL, headers=headers, json=body, timeout=30)
                    r.raise_for_status()
                    answer = r.json()["choices"][0]["message"]["content"]
                    st.success(answer)
                except requests.RequestException as e:
                    st.error(f"OpenAI-Fehler: {e}")

# --- Sidebar ---
st.sidebar.header("ℹ️ Info und Sicherheit")
st.sidebar.markdown(
    """
    • Legen Sie Ihre Meilisearch- und OpenAI-Zugangsdaten in Streamlit Secrets ab.
    • Öffnen Sie unter Streamlit Cloud: *Manage App > Secrets*.
    • Fügen Sie ein JSON-Dokument mit den Schlüssel-Wert-Paaren hinzu.
    """
)
st.sidebar.markdown(f"**Meilisearch Index:** `{MEILI_INDEX}`")
st.sidebar.markdown(f"**KI-Modell:** `{OPENAI_MODEL}`")
