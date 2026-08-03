/* ============================================================================
 * pull_funnel_detail.js  —  MANUAL browser pull of the per-event funnel detail
 * ----------------------------------------------------------------------------
 * The active-funnel record bodies (which specific events are at each stage) are
 * NOT available to the Application Password / GitHub Actions. They only come
 * through a logged-in browser session. This snippet pulls them for you.
 *
 * HOW TO RUN
 *   1. Log in to https://central.wordcamp.org with your admin account.
 *   2. Open any wp-admin page there, e.g. https://central.wordcamp.org/wp-admin/
 *   3. Open the browser DevTools console (F12 / Cmd-Opt-J) and paste this whole
 *      file, then press Enter.
 *   4. It downloads "funnel_detail.json". Move that file into the repo root and
 *      run:  python3 api/merge_funnel_detail.py funnel_detail.json
 *
 * It reads only your own logged-in permissions and downloads group/event-level
 * data (no member PII). Nothing is uploaded anywhere.
 * ==========================================================================*/
(async () => {
  const nonce = (window.wpApiSettings && wpApiSettings.nonce)
    || document.querySelector('#wpApiSettings')?.textContent
    || null;
  if (!nonce) {
    console.error("No REST nonce found. Run this on a central.wordcamp.org/wp-admin page while logged in.");
    return;
  }
  const FUNNEL = [
    ["wcpt-needs-vetting", "Needs Vetting"], ["wcpt-needs-orientati", "Needs Orientation/Interview"],
    ["wcpt-more-info-reque", "On Hold (more info)"], ["wcpt-interview-sched", "Interview Scheduled"],
    ["wcpt-approved-pre-pl", "Approved for Pre-Planning"], ["wcpt-pre-planning", "In Pre-Planning"],
    ["wcpt-needs-budget-re", "Needs Budget Review"], ["wcpt-budget-rev-sche", "Budget Review Scheduled"],
    ["wcpt-needs-contract", "Needs Contract"], ["wcpt-needs-fill-list", "Needs Listing"],
    ["wcpt-needs-schedule", "Needs Schedule"],
  ];
  const fmtType = (t) => {
    const s = (t || "").toLowerCase();
    if (s.includes("campus connect")) return "Campus Connect";
    if (s.includes("student club")) return "Student Club";
    if (s.includes("do_action") || s.includes("doaction")) return "do_action";
    if (s.includes("women") && (s.includes("wordpress") || s.includes("wp"))) return "Women WP Day";
    if (s.includes("wordcamp")) return "WordCamp";
    return "Other";
  };
  const recs = [];
  for (const [slug, stage] of FUNNEL) {
    let page = 1;
    while (true) {
      const url = `/wp-json/wp/v2/wordcamps?status=${slug}&per_page=100&page=${page}&context=edit`;
      let res;
      try { res = await fetch(url, { credentials: "include", headers: { "X-WP-Nonce": nonce } }); }
      catch (e) { console.warn(slug, "fetch failed", e); break; }
      if (!res.ok) { if (res.status === 400 && page > 1) break; console.warn(slug, "->", res.status); break; }
      const batch = await res.json();
      if (!Array.isArray(batch) || !batch.length) break;
      for (const r of batch) {
        const title = (r.title && (r.title.rendered || r.title.raw)) || "";
        const loc = r["Location"] || r["_venue_country_name"] || "";
        const country = (loc.split(",").pop() || "").trim();
        const ts = r["Start Date (YYYY-mm-dd)"];
        recs.push({
          id: r.id, slug, stage, title,
          start: ts ? new Date(+ts * 1000).toISOString().slice(0, 10) : null,
          location: loc, organizer: r["Organizer Name"] || "", anticipated: r["Number of Anticipated Attendees"] || "",
          link: r.link || "", format: fmtType(title), country,
          us: /(usa|united states)/i.test(country), test: /test/i.test(title),
        });
      }
      if (batch.length < 100) break;
      page++;
    }
  }
  const out = { asOf: new Date().toISOString().slice(0, 10), records: recs };
  const blob = new Blob([JSON.stringify(out, null, 1)], { type: "application/json" });
  const a = document.createElement("a");
  a.href = URL.createObjectURL(blob); a.download = "funnel_detail.json"; a.click();
  console.log(`Pulled ${recs.length} funnel records (as of ${out.asOf}). Saved funnel_detail.json — now run: python3 api/merge_funnel_detail.py funnel_detail.json`);
})();
