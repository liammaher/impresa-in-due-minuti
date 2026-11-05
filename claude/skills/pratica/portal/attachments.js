// The draft's attachments as the portal holds them: one JavaScript call on the open draft returns,
// for each file, its slot's title, its name, size and SHA-256, each fetched back from
// /fnsuap/download.do with the person's session. review.py matches them to the job's files.
//
// Only the "Allega documenti" screen lists them: on another screen it clicks that menu link and
// returns {opening: true}; call it again once the page has loaded. Seen on the CILA rehearsal
// 2026-11-05: 8 files, each the same bytes as the one attached (portal/README.md).
(async () => {
  try {
    const links = [...document.querySelectorAll('a[href*="download.do"]')];
    if (!links.length) {
      const menu = [...document.querySelectorAll("li a")].find((a) => /^allega documenti$/i.test(a.innerText.trim()));
      if (!menu) return { error: "no attachments here and no Allega Documenti link: is the draft open?" };
      setTimeout(() => menu.click(), 50);
      return { opening: true };
    }
    // A slot's title is the nearest row above its files that is no file, no "+", no blank and
    // not the "Tipologie ammesse" line (which closes the slot before).
    const slotOf = (a) => {
      for (let tr = a.closest("tr")?.previousElementSibling; tr; tr = tr.previousElementSibling) {
        if (tr.querySelector('a[href*="download.do"]')) continue;
        const t = tr.innerText.replace(/\s+/g, " ").trim();
        if (t && t !== "+" && !/^Tipologie ammesse/i.test(t) && t !== "Scarica il documento") return t;
      }
      return null;
    };
    const byId = new Map(); // each file has two links (its icon and its name)
    for (const a of links) {
      const id = new URL(a.href, location.href).searchParams.get("id");
      if (id && !byId.has(id)) byId.set(id, a);
    }
    const hex = (b) => [...new Uint8Array(b)].map((x) => x.toString(16).padStart(2, "0")).join("");
    const files = [];
    for (const [id, a] of byId) {
      const r = await fetch(a.href, { credentials: "include" });
      if (!r.ok) return { error: `the portal answered ${r.status} for file ${id}` };
      const b = await r.arrayBuffer();
      const disp = r.headers.get("content-disposition") || "";
      const name = (disp.match(/filename="?([^";]+)"?/) || [])[1] || a.closest("tr")?.querySelector(".upload-name")?.innerText.trim() || null;
      files.push({ slot: slotOf(a), name, size: b.byteLength, sha256: hex(await crypto.subtle.digest("SHA-256", b)) });
    }
    return { files };
  } catch (e) {
    return { error: `${e.name}: ${e.message}` };
  }
})()
