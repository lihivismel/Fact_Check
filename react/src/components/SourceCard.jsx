// src/components/SourceCard.jsx
// Card that shows one evidence source from the backend.

const TRUSTED_DOMAINS = [
  "www.ynet.co.il",
  "ynet.co.il",
  "www.clalit.co.il",
  "clalit.co.il",
  "www.haaretz.co.il",
  "haaretz.co.il",
  "www.health.gov.il",
  "health.gov.il"
];

export default function SourceCard({ source }) {
  // Safety: if source is missing or not an object, render nothing
  if (!source || typeof source !== "object") {
    return null;
  }

  // Extract useful fields from the source object
  const {
    url,
    domain,
    title,
    published_at,
    language,
    chunks,

    nli_evaluated,
    nli_max_entail,
    nli_max_contra,
    nli_best_ent_chunk,
    nli_best_contra_chunk
  } = source;

  // Derive final hostname to display, and to check trust
  let displayDomain = domain;
  if (!displayDomain && url) {
    try {
      displayDomain = new URL(url).hostname;
    } catch {
      // ignore invalid url
    }
  }

  // Determine if this domain is considered "trusted"
  const isTrusted = displayDomain
    ? TRUSTED_DOMAINS.includes(displayDomain.toLowerCase())
    : false;

  // Derive a "stance" label for the source, based on NLI scores:
  // - If entailment is high -> supports
  // - If contradiction is high -> contradicts
  // - Otherwise neutral / unclear
  let stance = "neutral";
  if (typeof nli_max_entail === "number" && nli_max_entail >= 0.5) {
    stance = "supports";
  } else if (typeof nli_max_contra === "number" && nli_max_contra >= 0.5) {
    stance = "contradicts";
  }

  // Pick which text snippet to highlight to the user
  let snippet = "";
  if (stance === "supports" && nli_best_ent_chunk) {
    snippet = nli_best_ent_chunk;
  } else if (stance === "contradicts" && nli_best_contra_chunk) {
    snippet = nli_best_contra_chunk;
  } else if (Array.isArray(chunks) && chunks.length > 0) {
    snippet = chunks[0];
  }

  // Format the date (published_at) if present
  let formattedDate = "";
  if (published_at) {
    const d = new Date(published_at);
    if (!Number.isNaN(d.valueOf())) {
      formattedDate = d.toLocaleDateString("en-GB");
    }
  }

  // Small badge style (stance)
  const badgeBase =
    "inline-block rounded-xl px-2 py-1 text-[11px] font-semibold border";
  const stanceBadgeStyles = {
    supports:
      badgeBase +
      " bg-green-50 text-green-700 border-green-300",
    contradicts:
      badgeBase +
      " bg-red-50 text-red-700 border-red-300",
    neutral:
      badgeBase +
      " bg-gray-50 text-gray-700 border-gray-300"
  };

  const stanceText =
    stance === "supports"
      ? "Supports the claim"
      : stance === "contradicts"
      ? "Contradicts the claim"
      : "Neutral / unclear";

  // Badge style for "Trusted source"
  const trustedBadge =
    "inline-block rounded-xl px-2 py-1 text-[10px] font-semibold border bg-blue-50 text-blue-700 border-blue-300";

  return (
    <a
      href={url}
      target="_blank"
      rel="noreferrer"
      className="block"
    >
      <div className="card p-4 hover:shadow-lg transition">
        {/* Top row: title + meta + badges */}
        <div className="flex flex-col gap-3 sm:flex-row sm:items-start sm:justify-between">
          {/* Left side: title + domain/date/lang + trusted */}
          <div className="min-w-0 flex-1">
            <div className="font-semibold text-sm leading-snug line-clamp-2">
              {title || displayDomain || url || "Untitled source"}
            </div>

            <div className="text-[11px] text-gray-600 mt-1 flex flex-wrap gap-x-2 gap-y-1 items-center">
              {displayDomain && <span>{displayDomain}</span>}
              {language && <span>• {language}</span>}
              {formattedDate && <span>• {formattedDate}</span>}
              {isTrusted && (
                <span className={trustedBadge}>
                  Trusted source
                </span>
              )}
            </div>
          </div>

          {/* Right side: stance badge */}
          <div className="flex-shrink-0">
            <span className={stanceBadgeStyles[stance]}>
              {stanceText}
            </span>
          </div>
        </div>

        {/* NLI scores (for transparency / debugging) */}
        {nli_evaluated && (
          <div className="text-[11px] text-gray-700 mt-2 flex flex-wrap gap-3">
            {typeof nli_max_entail === "number" && (
              <div>
                entail:{" "}
                <strong>{nli_max_entail.toFixed(2)}</strong>
              </div>
            )}
            {typeof nli_max_contra === "number" && (
              <div>
                contra:{" "}
                <strong>{nli_max_contra.toFixed(2)}</strong>
              </div>
            )}
          </div>
        )}

        {/* Main snippet */}
        {snippet && (
          <div className="text-xs text-gray-800 bg-gray-50 rounded-xl p-3 mt-3 line-clamp-3">
            {snippet}
          </div>
        )}
      </div>
    </a>
  );
}
