// api.js
export async function verifyClaim(claim) {
  if (typeof claim !== "string" || !claim.trim()) {
    throw new Error("Claim must be a non-empty string");
  }

  const PATH = "/api/verify"; 

  const res = await fetch(PATH, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ claim }) 
  });

  if (!res.ok) {
    const txt = await res.text().catch(() => "");
    throw new Error(`HTTP ${res.status} ${res.statusText} — ${txt.slice(0, 300)}`);
  }
  return res.json();
}