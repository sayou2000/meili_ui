import streamlit as st
import meilisearch
import os
import re
from openai import OpenAI

# === Konfiguration ===
MEILI_URL = "https://search.plgrnd.de"
MEILI_API_KEY = os.getenv("MEILI_API_KEY")
INDEX_NAME = "testdokumente"

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
openai_client = OpenAI(api_key=OPENAI_API_KEY)

# === Verbindung Meilisearch ===
client = meilisearch.Client(MEILI_URL, MEILI_API_KEY)
index = client.index(INDEX_NAME)

# === Hilfsfunktion: relevante Textstellen extrahieren ===
def extract_snippets(text, query, context_length=200):
    keywords = query.lower().split()
    matches = [m.start() for k in keywords for m in re.finditer(re.escape(k), text.lower())]
    snippets = []

    for pos in sorted(matches[:5]):  # maximal 5 Treffer pro Dokument
        start = max(0, pos - context_length)
        end = min(len(text), pos + context_length)
        snippet = text[start:end].strip()
        snippets.append(f"...{snippet}...")

    return "\n\n".join(snippets) if snippets else text[:1000]

# === Streamlit UI ===
st.set_page_config(page_title="Dokumentenrecherche mit GPT", layout="wide")
st.title("🔎 Intelligente Dokumentensuche")

query = st.text_input("Was möchtest du wissen oder finden?")

if query:
    with st.spinner("Durchsuche Dokumente..."):
        results = index.search(query, {"limit": 5})

    docs = results.get("hits", [])

    if docs:
        st.subheader("📄 Ergebnisse:")
        for i, doc in enumerate(docs):
            with st.expander(f"{i+1}. {doc['filename']}"):
                relevant_snippets = extract_snippets(doc["content"], query)
                st.write(relevant_snippets)
                if st.button("🧠 GPT-Zusammenfassung", key=f"gpt_{i}"):
                    with st.spinner("Frage wird verarbeitet..."):
                        prompt = f"""Du bist ein Experte für technische Dokumentation. Der Nutzer hat folgende Frage: '{query}'. Hier sind relevante Textausschnitte aus einem Dokument:

{relevant_snippets}

Bitte beantworte die Frage basierend auf diesen Textstellen."""
                        try:
                            response = openai_client.chat.completions.create(
                                model="o4-mini-2025-04-16",
                                messages=[
                                    {"role": "system", "content": "Du hilfst bei der Auswertung technischer Dokumente."},
                                    {"role": "user", "content": prompt}
                                ]
                            )
                            answer = response.choices[0].message.content
                            st.success("Antwort:")
                            st.markdown(answer)
                        except Exception as e:
                            st.error(f"Fehler bei OpenAI: {e}")
    else:
        st.warning("Keine Treffer gefunden.")

st.sidebar.markdown("---")
st.sidebar.info("Diese Anwendung verbindet Meilisearch und GPT zur intelligenten Dokumentenanalyse.")
