// App.jsx
// Minimal UI: enter a claim, send to backend, show result & sources.

import { useState } from "react";
import { verifyClaim } from "./api.js";
import Gauge from "./components/Gauge.jsx";
import SourceCard from "./components/SourceCard.jsx";

export default function App() {
  // Local UI state
  const [claim, setClaim] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  const [result, setResult] = useState(null);

  // Normalize backend score for the gauge display (0-100%)
  function normalizeScoreForGauge(raw) {
    const num = Number(raw);
    if (!Number.isFinite(num)) {
      return 0;
    }
    // If backend score is <1 we assume it's 0..1 and convert to %
    // If backend score is already >=1 we assume it's already a %
    const pct = num < 1 ? num * 100 : num;
    const clamped = Math.max(0, Math.min(100, pct));
    return Math.round(clamped);
  }

  // Handle the submit event
  async function onSubmit(e) {
    e.preventDefault();           // Prevent full page reload
    setError("");
    setResult(null);
    setLoading(true);
    try {
      const data = await verifyClaim(claim); // Call backend
      setResult(data);                       // Save server response
    } catch (err) {
      setError(err.message || "Unexpected error");
    } finally {
      setLoading(false);
    }
  }

  // Compute the gaugeValue directly from the backend result
  const gaugeValue = normalizeScoreForGauge(result?.score);

  return (
    <div className="container-rtl py-8">
      {/* Header */}
      <header className="mb-6">
        <h1 className="text-3xl font-extrabold tracking-tight flex items-center gap-2">
          <span role="img" aria-label="brain">🧠</span>
          <span>FactCheck</span>
        </h1>
        <p className="text-gray-600 mt-2 text-sm leading-relaxed">
          Enter any factual claim, click "Verify claim", and we'll search
          sources, analyze stance, and score confidence.
        </p>
      </header>

      {/* Form card */}
      <section className="card p-5 mb-6">
        <form onSubmit={onSubmit} className="flex flex-col gap-3">
          <label className="text-sm font-medium text-gray-700">
            Claim to verify
          </label>

          <textarea
            className="input min-h-[100px] resize-y"
            placeholder='Example: "The flu vaccine reduces severe illness in adults 65+" (can also be Hebrew)'
            value={claim}
            onChange={(e) => setClaim(e.target.value)}
          />

          <div className="flex items-center gap-3">
            <button
              className="btn-primary"
              type="submit"
              disabled={loading || !claim.trim()}
            >
              Verify claim
            </button>

            {loading && (
              <span className="text-sm text-gray-600">
                Checking sources and running NLI...
              </span>
            )}
          </div>
        </form>
      </section>

      {/* Error box */}
      {error && (
        <div className="card p-4 mb-6 border-red-200 bg-red-50 text-red-800 text-sm">
          ⚠️ {error}
        </div>
      )}

      {/* Result */}
      {result && (
        <section className="card p-5">
          <h2 className="text-lg font-semibold mb-3">Result</h2>

          {/* Gauge + explanation side by side */}
          <div className="flex flex-col lg:flex-row lg:items-start lg:justify-between gap-6 mb-6">

            {/* Gauge area */}
            <div className="flex-1 lg:max-w-sm">
              <div className="text-xs font-semibold text-gray-500 uppercase tracking-wide mb-2">
                Overall confidence
              </div>

              {/* Pass final numeric % into the gauge */}
              <Gauge value={gaugeValue} />

              <div className="text-center text-sm text-gray-700 mt-2">
                {gaugeValue}% confidence
              </div>
            </div>

            {/* Meta info (raw backend data) */}
            <div className="flex-1 text-sm text-gray-700 space-y-2">
              {"claim" in result && (
                <div>
                  <span className="font-semibold">Claim:</span>{" "}
                  <span className="break-words">{result.claim}</span>
                </div>
              )}

              {"score" in result && (
                <div>
                  <span className="font-semibold">Score:</span>{" "}
                  <span>{String(result.score)}</span>
                </div>
              )}

              {"unique_domains" in result && (
                <div>
                  <span className="font-semibold">number of domains:</span>{" "}
                  <span>{result.unique_domains}</span>
                </div>
              )}

              {/* We intentionally hide coverage_bucket here if it's confusing.
                  You can re-enable later if you want. */}

              {"notes" in result && result.notes && (
                <div className="text-xs text-gray-600 leading-relaxed">
                  <span className="font-semibold">Notes:</span>{" "}
                  <em>{result.notes}</em>
                </div>
              )}

              {/* Explanation for humans
              <div className="text-[11px] text-gray-500 leading-relaxed pt-2 border-t border-gray-200">
                This score blends:
                <ul className="list-disc pl-4 mt-1 space-y-1">
                  <li>
                    Text evidence that supports or contradicts the claim
                    (NLI entailment vs. contradiction).
                  </li>
                  <li>
                    Source credibility and freshness (trusted domains,
                    recent publish date).
                  </li>
                  <li>
                    Breadth of coverage (how many different domains mention it).
                  </li>
                </ul>
              </div> */}
            </div>
          </div>

          {/* Sources */}
          <div className="space-y-3">
            <h3 className="text-base font-semibold">Sources</h3>

            {Array.isArray(result.sources) && result.sources.length > 0 ? (
              result.sources.map((s, idx) => (
                <SourceCard key={idx} source={s} />
              ))
            ) : (
              <div className="text-sm text-gray-500">
                No sources found.
              </div>
            )}
          </div>

          {/* Debug JSON view
          <div className="mt-6">
            <h3 className="text-sm font-medium text-gray-700 mb-2">
              Full JSON (debug view)
            </h3>
            <pre className="text-xs bg-gray-50 p-3 rounded-xl overflow-auto">
              {JSON.stringify(result, null, 2)}
            </pre>
          </div> */}
        </section>
      )}
    </div>
  );
}
