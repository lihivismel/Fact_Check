// App.jsx
// Minimal form that sends a claim to the backend and shows the response.

import { useState } from "react";
import { verifyClaim } from "./api.js";

export default function App() {
  // Local UI state
  const [claim, setClaim] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  const [result, setResult] = useState(null);

  // Handle the submit event
  async function onSubmit(e) {
    e.preventDefault();           // Prevent full page reload
    setError("");
    setResult(null);
    setLoading(true);
    try {
      const data = await verifyClaim(claim); // Call our API helper
      setResult(data);                       // Save server response for rendering
    } catch (err) {
      setError(err.message || "Unexpected error");
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="container-rtl py-8">
      {/* Header */}
      <header className="mb-6">
        <h1 className="text-3xl font-extrabold tracking-tight">🧠 FactCheck</h1>
        <p className="text-gray-600 mt-2">
          הזן טענה ולחץ על אימות
        </p>
      </header>

      {/* Form card */}
      <section className="card p-5 mb-6">
        <form onSubmit={onSubmit} className="flex flex-col gap-3">
          <label className="text-sm font-medium text-gray-700">הטענה לבדיקה</label>
          <textarea
            className="input min-h-[100px] resize-y"
            placeholder="לדוגמה: חיסון השפעת מפחית תחלואה קשה בקרב בני 65+"
            value={claim}
            onChange={(e) => setClaim(e.target.value)}
          />
          <div className="flex items-center gap-3">
            <button
              className="btn-primary"
              type="submit"
              disabled={loading || !claim.trim()}
            >
              אימות הטענה
            </button>
            {loading && <span className="text-sm text-gray-600">מריץ חיפוש ו-NLI...</span>}
          </div>
        </form>
      </section>

      {/* Error box */}
      {error && (
        <div className="card p-4 mb-6 border-red-200 bg-red-50 text-red-800">
          ⚠️ {error}
        </div>
      )}

      {/* Result card — adapted to backend schema */}
      {result && (
        <section className="card p-5">
          <h2 className="text-lg font-semibold mb-3">תוצאה ראשונית</h2>

          {/* Top summary fields */}
          <div className="text-sm text-gray-700 space-y-1 mb-4">
            {"claim" in result && (
              <div>הטענה: <span className="font-medium">{result.claim}</span></div>
            )}
            {"score" in result && (
              <div>ציון: <strong>{Math.round(result.score)}</strong></div>
            )}
            {"unique_domains" in result && (
              <div>מס׳ דומיינים ייחודיים: <strong>{result.unique_domains}</strong></div>
            )}
            {"coverage_bucket" in result && result.coverage_bucket && (
              <div>כיסוי: <strong>{result.coverage_bucket}</strong></div>
            )}
            {"notes" in result && result.notes && (
              <div>הערות: <em>{result.notes}</em></div>
            )}
          </div>

          {/* Sources (EvidenceItem[]) */}
          <div className="space-y-3">
            <h3 className="text-base font-semibold">מקורות</h3>

            {Array.isArray(result.sources) && result.sources.length > 0 ? (
              result.sources.map((s, idx) => (
                <a
                  key={idx}
                  href={s.url}
                  target="_blank"
                  rel="noreferrer"
                  className="block"
                >
                  <div className="card p-4 hover:shadow transition">
                    <div className="flex items-center justify-between gap-3">
                      <h4 className="font-semibold line-clamp-1">
                        {s.title || s.domain || s.url}
                      </h4>
                      {s.published_at && (
                        <span className="text-xs text-gray-600">
                          {new Date(s.published_at).toLocaleDateString("he-IL")}
                        </span>
                      )}
                    </div>

                    <div className="text-xs text-gray-600 mt-1">
                      {s.domain && <span>{s.domain}</span>}
                      {!s.domain && s.url && <span>{new URL(s.url).hostname}</span>}
                      {s.language && <span> • {s.language}</span>}
                    </div>

                    {/* NLI details if present */}
                    <div className="mt-2 text-xs text-gray-700 space-y-1">
                      {s.nli_evaluated === true && (
                        <div className="text-green-700">
                          NLI evaluated
                        </div>
                      )}
                      {typeof s.nli_max_entail === "number" && (
                        <div>max_entail: <strong>{s.nli_max_entail.toFixed(2)}</strong></div>
                      )}
                      {typeof s.nli_max_contra === "number" && (
                        <div>max_contra: <strong>{s.nli_max_contra.toFixed(2)}</strong></div>
                      )}
                      {s.nli_best_ent_chunk && (
                        <div className="line-clamp-2">
                          best_ent_chunk: “{s.nli_best_ent_chunk}”
                        </div>
                      )}
                      {s.nli_best_contra_chunk && (
                        <div className="line-clamp-2">
                          best_contra_chunk: “{s.nli_best_contra_chunk}”
                        </div>
                      )}
                    </div>

                    {/* Show first chunk as preview if exists */}
                    {Array.isArray(s.chunks) && s.chunks.length > 0 && (
                      <div className="mt-3 text-xs text-gray-700 bg-gray-50 rounded-xl p-3">
                        {s.chunks[0]}
                      </div>
                    )}
                  </div>
                </a>
              ))
            ) : (
              <div className="text-sm text-gray-500">לא נמצאו מקורות.</div>
            )}
          </div>

          {/* Raw JSON for learning/debugging (can remove later) */}
          <div className="mt-4">
            <h3 className="text-sm font-medium text-gray-700 mb-2">JSON מלא (ללימוד/בדיקה):</h3>
            <pre className="text-xs bg-gray-50 p-3 rounded-xl overflow-auto">
              {JSON.stringify(result, null, 2)}
            </pre>
          </div>
        </section>
      )}
    </div>
  );
}
