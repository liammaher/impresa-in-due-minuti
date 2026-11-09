// The portal's preview PDF as text, in the pane, with no Python and no pdf.js: one JavaScript
// call on a page of an open draft returns the text of /fnsuap/preview.do, a line per row, the
// cells of a row joined by two spaces, tick boxes as "[ X ]" / "[  ]", each page headed
// "--- pagina N". First run 2026-11-05 (portal/README.md, "The preview as text"); offline test:
// bench/test_preview_text.py.
//
// The preview is iText 2.1.7: Flate streams, simple fonts in WinAnsi, text placed by Tm. This
// reads that and the usual variants (TJ, ', ", T*, TL, cm, hex strings, an indirect /Length).
// What it can't read faithfully (object streams, encryption, CID or remapped fonts, form
// XObjects, a filter other than Flate) returns {error}, never a wrong or partial text.
(async () => {
  const fail = (m) => { throw Object.assign(new Error(m), { name: "PreviewError" }); };
  try {
    const r = await fetch("/fnsuap/preview.do", { credentials: "include" });
    const buf = new Uint8Array(await r.arrayBuffer());
    const s = new TextDecoder("latin1").decode(buf); // one char per byte: indexes are offsets
    if (!s.startsWith("%PDF-")) fail(`the portal sent no PDF (HTTP ${r.status}): the session may have ended`);

    // Objects, skipping each stream's bytes so nothing inside one reads as an object.
    const dicts = {}, streams = {}, plain = {};
    const skipString = (i) => { // s[i] === "(": index after its balanced ")"
      for (let depth = 0; i < s.length; i++) {
        if (s[i] === "\\") i++;
        else if (s[i] === "(") depth++;
        else if (s[i] === ")" && --depth === 0) return i + 1;
      }
      fail("an unterminated string in the PDF");
    };
    const skipDict = (i) => { // s.startsWith("<<", i): index after its balanced ">>"
      for (let depth = 0; i < s.length;) {
        if (s.startsWith("<<", i)) { depth++; i += 2; }
        else if (s.startsWith(">>", i)) { i += 2; if (--depth === 0) return i; }
        else if (s[i] === "(") i = skipString(i);
        else if (s[i] === "<") { const e = s.indexOf(">", i); i = e < 0 ? s.length : e + 1; } // a hex string
        else i++;
      }
      fail("an unterminated dictionary in the PDF");
    };
    const objRe = /(\d+)\s+\d+\s+obj\b\s*/g;
    for (let m; (m = objRe.exec(s));) {
      const n = m[1], at = objRe.lastIndex;
      if (!s.startsWith("<<", at)) {
        const end = s.indexOf("endobj", at);
        plain[n] = s.slice(at, end < 0 ? at : end).trim();
        continue;
      }
      const dictEnd = skipDict(at);
      dicts[n] = s.slice(at, dictEnd);
      const st = /^\s*stream(\r\n|\n|\r)/.exec(s.slice(dictEnd, dictEnd + 12));
      if (!st) { objRe.lastIndex = dictEnd; continue; }
      const start = dictEnd + st[0].length;
      // \b: "/Length 12 0 R" must not read as a direct length of 1.
      const direct = dicts[n].match(/\/Length\s+(\d+)\b(?!\s+\d+\s+R)/);
      const ends = (e) => /^\s*endstream/.test(s.slice(e, e + 20));
      let end = direct && ends(start + +direct[1]) ? start + +direct[1] : -1;
      if (end < 0) { // an indirect or wrong /Length: up to endstream, less the line break before it
        end = s.indexOf("endstream", start);
        if (end < 0) fail("a stream with no end in the PDF");
        objRe.lastIndex = end;
        if (s[end - 1] === "\n") end--;
        if (s[end - 1] === "\r") end--;
      } else objRe.lastIndex = end;
      streams[n] = { start, end, ref: direct ? null : (dicts[n].match(/\/Length\s+(\d+)\s+\d+\s+R/) || [])[1] };
    }
    for (const st of Object.values(streams)) // an indirect /Length, once every object is known
      if (st.ref && /^\d+$/.test(plain[st.ref] || "") && /^\s*endstream/.test(s.slice(st.start + +plain[st.ref], st.start + +plain[st.ref] + 20)))
        st.end = st.start + +plain[st.ref];

    const all = Object.values(dicts).join("\n");
    const trailer = s.slice(s.lastIndexOf("trailer"));
    if (/\/Encrypt\b/.test(all) || /\/Encrypt\b/.test(trailer)) fail("the PDF is encrypted");
    if (/\/Type\s*\/ObjStm\b/.test(all)) fail("the PDF keeps objects in compressed streams");
    // Text inside a form XObject would be missed: refused where a page draws one (Do).
    const hasForm = /\/Subtype\s*\/Form\b/.test(all);
    for (const d of Object.values(dicts).filter((d) => /\/Type\s*\/Font\b/.test(d))) {
      if (/\/Subtype\s*\/(Type0|Type3)\b/.test(d) || /\/Differences\b/.test(d) || /\/ToUnicode\b/.test(d)
          || (/\/Encoding\b/.test(d) && !/\/Encoding\s*\/WinAnsiEncoding\b/.test(d)))
        fail("the PDF has a font this reader can't decode");
    }

    const decode = async (n) => {
      const st = streams[n] || fail(`page content ${n} is missing`);
      const bytes = buf.slice(st.start, st.end);
      const f = (dicts[n].match(/\/Filter\s*(\[[^\]]*\]|\/\w+)/) || [])[1] || "";
      const filters = f.match(/\/\w+/g) || [];
      if (!filters.length) return bytes;
      if (filters.length > 1 || !/^\/(FlateDecode|Fl)$/.test(filters[0])) fail(`a stream filter this reader doesn't know (${f})`);
      try {
        return new Uint8Array(await new Response(new Blob([bytes]).stream().pipeThrough(new DecompressionStream("deflate"))).arrayBuffer());
      } catch (e) { fail("a page's content doesn't decompress"); }
    };
    const refs = (str) => [...str.matchAll(/(\d+)\s+\d+\s+R/g)].map((x) => x[1]);

    // Pages in reading order, from the catalog's page tree.
    const catalog = Object.values(dicts).find((d) => /\/Type\s*\/Catalog\b/.test(d)) || fail("the PDF has no catalog");
    const pages = [], seen = new Set();
    (function walk(n) {
      if (seen.has(n)) fail("the PDF's page tree loops");
      seen.add(n);
      const d = dicts[n] || fail(`page object ${n} is missing`);
      if (/\/Type\s*\/Pages\b/.test(d)) refs((d.match(/\/Kids\s*\[([^\]]*)\]/) || fail("a page list with no Kids"))[1]).forEach(walk);
      else if (/\/Type\s*\/Page\b/.test(d)) pages.push(n);
    })(refs((catalog.match(/\/Pages\s+\d+\s+\d+\s+R/) || fail("the catalog names no pages"))[0])[0]);
    if (!pages.length) fail("the PDF has no pages");

    // A page's content, as tokens: numbers, strings (bytes), names, arrays, operators.
    const W1252 = new TextDecoder("windows-1252"); // also one char per byte, for ASCII words
    const ascii = (c, a, b) => W1252.decode(c.subarray(a, b));
    function* tokens(c) {
      const isWs = (ch) => ch === 0x20 || ch === 0x0a || ch === 0x0d || ch === 0x09 || ch === 0x0c || ch === 0x00;
      const delim = "()<>[]{}/%";
      let i = 0;
      while (i < c.length) {
        const ch = c[i];
        if (isWs(ch)) { i++; continue; }
        const k = String.fromCharCode(ch);
        if (k === "%") { while (i < c.length && c[i] !== 0x0a && c[i] !== 0x0d) i++; continue; }
        if (k === "(") {
          const out = [];
          let depth = 1;
          for (i++; i < c.length && depth;) {
            const b = c[i++];
            if (b === 0x5c) { // backslash
              const e = c[i++];
              const map = { 0x6e: 10, 0x72: 13, 0x74: 9, 0x62: 8, 0x66: 12 };
              if (e in map) out.push(map[e]);
              else if (e >= 0x30 && e <= 0x37) {
                let v = e - 0x30;
                for (let j = 0; j < 2 && c[i] >= 0x30 && c[i] <= 0x37; j++) v = v * 8 + c[i++] - 0x30;
                out.push(v & 0xff);
              } else if (e === 0x0d) { if (c[i] === 0x0a) i++; } // line continuation
              else if (e !== 0x0a) out.push(e);
            } else if (b === 0x28) { depth++; out.push(b); }
            else if (b === 0x29) { if (--depth) out.push(b); }
            else out.push(b);
          }
          yield { str: out };
          continue;
        }
        if (k === "<" && c[i + 1] === 0x3c) { // an inline dict (marked content): skip it whole
          let depth = 0;
          while (i < c.length) {
            if (c[i] === 0x3c && c[i + 1] === 0x3c) { depth++; i += 2; }
            else if (c[i] === 0x3e && c[i + 1] === 0x3e) { i += 2; if (!--depth) break; }
            else i++;
          }
          yield { dict: true };
          continue;
        }
        if (k === "<") {
          const end = c.indexOf(0x3e, i);
          let hex = ascii(c, i + 1, end < 0 ? c.length : end).replace(/\s+/g, "");
          if (hex.length % 2) hex += "0";
          yield { str: hex.match(/../g)?.map((h) => parseInt(h, 16)) || [] };
          i = end < 0 ? c.length : end + 1;
          continue;
        }
        if (k === "[" || k === "]") { yield { op: k }; i++; continue; }
        let j = i + (k === "/" ? 1 : 0);
        while (j < c.length && !isWs(c[j]) && !delim.includes(String.fromCharCode(c[j]))) j++;
        const word = ascii(c, i, Math.max(j, i + 1));
        i = Math.max(j, i + 1);
        if (k === "/") yield { name: word };
        else if (/^[+-]?(\d+\.?\d*|\.\d+)$/.test(word)) yield { num: +word };
        else if (word === "ID") { // inline image data: skip to EI
          const m = /\sEI(?=\s|$)/.exec(ascii(c, i, c.length));
          i = m ? i + m.index + 3 : c.length;
        } else yield { op: word };
      }
    }

    const mul = (m, n) => [m[0] * n[0] + m[1] * n[2], m[0] * n[1] + m[1] * n[3], m[2] * n[0] + m[3] * n[2],
      m[2] * n[1] + m[3] * n[3], m[4] * n[0] + m[5] * n[2] + n[4], m[4] * n[1] + m[5] * n[3] + n[5]];
    const I = [1, 0, 0, 1, 0, 0];
    const out = [];
    for (const [pi, p] of pages.entries()) {
      const contents = dicts[p].match(/\/Contents\s*(\[[^\]]*\]|\d+\s+\d+\s+R)/);
      const parts = contents ? await Promise.all(refs(contents[1]).map(decode)) : [];
      const c = new Uint8Array(parts.reduce((a, b) => a + b.length + 1, 0));
      let o = 0;
      for (const b of parts) { c.set(b, o); o += b.length; c[o++] = 0x0a; }

      const items = [];
      let ctm = I, stack = [], tm = I, tlm = I, lead = 0, moved = true, ops = [], arr = null;
      const show = (bytes) => {
        const t = W1252.decode(Uint8Array.from(bytes));
        const pos = mul(tm, ctm);
        if (!moved && items.length) items[items.length - 1].s += t; // same run: no gap
        else items.push({ x: pos[4], y: pos[5], s: t });
        moved = false;
      };
      const td = (tx, ty) => { tlm = mul([1, 0, 0, 1, tx, ty], tlm); tm = tlm; moved = true; };
      for (const t of tokens(c)) {
        if (t.op === "[") { arr = []; continue; }
        if (t.op === "]") { ops.push({ arr: arr || [] }); arr = null; continue; }
        if (arr && !t.op) { arr.push(t); continue; }
        if (!t.op) { ops.push(t); continue; }
        const n = ops.map((x) => x.num);
        switch (t.op) {
          case "Do": if (hasForm) fail("the PDF draws part of a page from a form XObject"); break;
          case "q": stack.push(ctm); break;
          case "Q": ctm = stack.pop() || I; break;
          case "cm": if (n.length >= 6) ctm = mul(n.slice(-6), ctm); break;
          case "BT": tm = tlm = I; moved = true; break;
          case "Tm": if (n.length >= 6) { tm = tlm = n.slice(-6); moved = true; } break;
          case "Td": td(n[n.length - 2] || 0, n[n.length - 1] || 0); break;
          case "TD": lead = -(n[n.length - 1] || 0); td(n[n.length - 2] || 0, n[n.length - 1] || 0); break;
          case "TL": lead = n[n.length - 1] || 0; break;
          case "T*": td(0, -lead); break;
          case "Tj": { const x = ops[ops.length - 1]; if (x && x.str) show(x.str); break; }
          case "'": case "\"": { td(0, -lead); const x = ops[ops.length - 1]; if (x && x.str) show(x.str); break; }
          case "TJ": {
            const a = (ops[ops.length - 1] || {}).arr || [];
            const bytes = [];
            for (const e of a) if (e.str) bytes.push(...e.str); else if (e.num < -200) bytes.push(0x20);
            show(bytes);
            break;
          }
        }
        ops = [];
      }

      // Rows by baseline (within 2 points: cells of one row can sit a fraction apart), then cells by x.
      items.sort((a, b) => b.y - a.y);
      const rows = [];
      for (const it of items) {
        const row = rows[rows.length - 1];
        if (row && Math.abs(row.y - it.y) <= 2) row.items.push(it);
        else rows.push({ y: it.y, items: [it] });
      }
      out.push(`--- pagina ${pi + 1}\n` + rows.map((r) => r.items.sort((a, b) => a.x - b.x).map((i) => i.s).join("  ")).join("\n"));
    }
    return { pages: pages.length, bytes: buf.length, text: out.join("\n") };
  } catch (e) {
    return { error: e.name === "PreviewError" ? e.message : `${e.name}: ${e.message}` };
  }
})()
