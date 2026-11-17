/** Fire a GoatCounter UI event. No-op until the page script defines __gcTrack. */
export function gcEvent(name: string, title?: string) {
  const track = (window as unknown as { __gcTrack?: (n: string, t?: string) => void }).__gcTrack;
  if (typeof track === "function") track(name, title);
}

export function gcSearch(query: string, hasResults: boolean) {
  const q = query.trim().slice(0, 50);
  gcEvent(
    hasResults ? "search-results" : "search-no-results",
    (hasResults ? "Search with results: " : "Search with no results: ") + q,
  );
}
