import streamlit as st
import meilisearch
import openai
import os

# === Konfiguration ===
MEILI_URL = "https://search.plgrnd.de"
MEILI_API_KEY = os.getenv("MEILI_API_KEY")
INDEX_NAME = "testdokumente"

openai.api_key = os.getenv("OPENAI_API_KEY")

# === Verbindung Meilisearch ===
client = meilisearch.Client(MEILI_URL, MEILI_API_KEY)
index = client.index(INDEX_NAME)

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
                snippet = doc["content"][:1000] + ("..." if len(doc["content"]) > 1000 else "")
                st.write(snippet)
                if st.button("🧠 GPT-Zusammenfassung", key=f"gpt_{i}"):
                    with st.spinner("Frage wird verarbeitet..."):
                        prompt = f"""Du bist ein Experte für technische Dokumentation. Der Nutzer hat folgende Frage: '{query}'. Hier ist ein Auszug aus einem Dokument:

{snippet}

Bitte beantworte die Frage basierend auf diesem Text."""
                        try:
                            response = openai.ChatCompletion.create(
                                model="gpt-4",
                                messages=[
                                    {"role": "system", "content": "Du hilfst bei der Auswertung technischer Dokumente."},
                                    {"role": "user", "content": prompt}
                                ]
                            )
                            answer = response["choices"][0]["message"]["content"]
                            st.success("Antwort:")
                            st.markdown(answer)
                        except Exception as e:
                            st.error(f"Fehler bei OpenAI: {e}")
    else:
        st.warning("Keine Treffer gefunden.")

st.sidebar.markdown("---")
st.sidebar.info("Diese Anwendung verbindet Meilisearch und GPT zur intelligenten Dokumentenanalyse.")
