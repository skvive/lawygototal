/** PAN public funnel events → POST /api/growth/events (cookie-based visitor hash, no PII). */
const panGrowthSent = new Set();
function panTrack(postId, eventType) {
  if (!postId || panGrowthSent.has(postId + "|" + eventType)) return;
  panGrowthSent.add(postId + "|" + eventType);
  fetch("/api/growth/events", {
    method: "POST",
    credentials: "same-origin",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ post_id: postId, event_type: eventType }),
  }).catch(() => {});
}
window.panTrack = panTrack;
