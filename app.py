import React, { useState, useCallback } from 'react';
import { Search, FileText, Brain, Loader2, AlertCircle } from 'lucide-react';

const MeilisearchFrontend = () => {
  const [query, setQuery] = useState('');
  const [results, setResults] = useState([]);
  const [loading, setLoading] = useState(false);
  const [aiResponses, setAiResponses] = useState({});
  const [aiLoading, setAiLoading] = useState({});
  const [error, setError] = useState('');

  // Konfiguration (als Umgebungsvariablen hinterlegen)
  const MEILI_URL = process.env.REACT_APP_MEILI_URL;
  const MEILI_API_KEY = process.env.REACT_APP_MEILI_API_KEY;
  const INDEX_NAME = 'testdokumente';

  const searchDocuments = useCallback(async () => {
    if (!query.trim()) return;
    setLoading(true);
    setError('');
    try {
      const searchParams = {
        q: query,
        limit: 10,
        attributesToHighlight: ['content'],
        highlightPreTag: '<mark class="bg-yellow-200 font-semibold">',
        highlightPostTag: '</mark>',
        attributesToSnippet: ['content:250'],
        snippetEllipsisText: '...'
      };
      const response = await fetch(
        `${MEILI_URL}/indexes/${INDEX_NAME}/search`,
        {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
            Authorization: `Bearer ${MEILI_API_KEY}`
          },
          body: JSON.stringify(searchParams)
        }
      );
      if (!response.ok) throw new Error(`HTTP error! status: ${response.status}`);
      const data = await response.json();
      setResults(data.hits || []);
      if (data.hits?.length === 0) setError('Keine Treffer gefunden.');
    } catch (err) {
      console.error('Search error:', err);
      setError('Fehler bei der Suche. Bitte überprüfen Sie die Verbindung zu Meilisearch.');
    } finally {
      setLoading(false);
    }
  }, [query]);

  const getAiSummary = async (docId, highlights) => {
    setAiLoading(prev => ({ ...prev, [docId]: true }));
    try {
      // Verwende die hervorgerufenen Snippets
      const relevantText = highlights._formatted?.content || '';
      const cleanText = relevantText.replace(/<mark[^>]*>|<\/mark>/g, '');
      const prompt = `Du bist ein Experte für Dokumentenanalyse.

Nutzerfrage: "${query}"

Relevante Textausschnitte:
${cleanText}

Bitte beantworte die Frage basierend ausschließlich auf diesen Textausschnitten und verweise präzise auf die Stellen.`;
      // OpenAI API-Aufruf
      const response = await fetch('/api/openai', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ prompt })
      });
      const result = await response.json();
      setAiResponses(prev => ({ ...prev, [docId]: result.answer }));
    } catch (err) {
      console.error('AI error:', err);
      setAiResponses(prev => ({ ...prev, [docId]: 'Fehler bei der AI-Analyse.' }));
    } finally {
      setAiLoading(prev => ({ ...prev, [docId]: false }));
    }
  };

  const handleKeyPress = e => {
    if (e.key === 'Enter') searchDocuments();
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-blue-50 to-indigo-100">
      <div className="container mx-auto px-4 py-8">
        <h1 className="text-4xl font-bold text-gray-800 mb-4">🔎 Intelligente Dokumentensuche</h1>
        <div className="flex gap-4 mb-6">
          <input
            type="text"
            value={query}
            onChange={e => setQuery(e.target.value)}
            onKeyPress={handleKeyPress}
            placeholder="Was möchten Sie wissen oder finden?"
            className="flex-1 pl-4 py-2 border rounded-lg"
          />
          <button
            onClick={searchDocuments}
            disabled={loading || !query.trim()}
            className="px-6 py-2 bg-blue-600 text-white rounded-lg disabled:opacity-50"
          >
            {loading ? <Loader2 className="animate-spin" /> : <Search />} Suchen
          </button>
        </div>
        {error && <div className="text-red-600 mb-4 flex items-center gap-2"><AlertCircle />{error}</div>}
        {results.length > 0 && (
          <div className="space-y-6">
            {results.map((doc, idx) => (
              <div key={doc.id || idx} className="bg-white p-6 rounded-lg shadow">
                <div className="flex justify-between items-center mb-4">
                  <h2 className="text-xl font-semibold">{doc._formatted?.filename || doc.filename}</h2>
                  <span className="text-sm text-gray-500">Relevanz: {Math.round(doc._matchesPosition?.content ? 100 : doc._formatted?.content.length / 250 * 100)}%</span>
                </div>
                <div className="prose mb-4" dangerouslySetInnerHTML={{ __html: doc._formatted?.content }} />
                <button
                  onClick={() => getAiSummary(doc.id || idx, doc)}
                  disabled={aiLoading[doc.id || idx]}
                  className="px-4 py-2 bg-purple-600 text-white rounded-lg disabled:opacity-50"
                >
                  {aiLoading[doc.id || idx] ? <Loader2 className="animate-spin" /> : <Brain />} KI-Analyse
                </button>
                {aiResponses[doc.id || idx] && (
                  <div className="mt-4 p-4 bg-purple-50 rounded-lg">
                    <h3 className="font-medium text-purple-800 mb-2">🧠 KI-Analyse:</h3>
                    <pre className="whitespace-pre-wrap text-purple-700">{aiResponses[doc.id || idx]}</pre>
                  </div>
                )}
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
};

export default MeilisearchFrontend;
