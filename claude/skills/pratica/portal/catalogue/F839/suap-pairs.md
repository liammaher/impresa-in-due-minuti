# SUAP: which operations the wizard takes together (probed 2026-11-13)

`catalogue.py pairs DIR --bundle FILE --suap`: each wedge sector's main operations (open, take over, move) with each
extra the library's SUAP table adds to them, on a scratch draft, through "Conferma" to the generated pratica. Never
filled, saved or sent. 53 pairs, 13 s each, **all 53 accepted, none refused**.

| Extra | Sectors | Adds to the pratica |
|---|---|---|
| Dehors, "Domanda di occupazione suolo pubblico per area annessa ad esercizio di somministrazione" | bars and restaurants, both zones | its adempimento (Comune) and its own sections (the area's measures, the period, the TOSAP/COSAP undertaking, the structure's assembly, the occupation's declaration) |
| PIN 2, SCIA prevenzione incendi | every sector probed | "SCIA per attività soggette ai controlli di prevenzione incendi" (Comando VV.F. - PRINCE) and 9 sections: six `SCIA VV.F. - ...`, the statistical information, **the professional's safety assessment (`ASSEVERAZIONE ... art. 4 DM 7.8.2012`) and the technical documents' list** |
| Sign, "SCIA per installazione insegna di esercizio" | every sector probed | its adempimento and 7 sections (the sign's declaration, place, characteristics, installation, project, works director, `ulteriori dichiarazioni (mezzi pubblicitari)`) |
| ASL notification, "avvio attività/trasferimento" | bars and restaurants, food shops | already part of an opening in the bar's sector; only a take-over adds it |

What it settles:

- The table's `also` role is right for all four: they are filed in the same pratica as the opening, take-over or move,
  not apart (a PIN is a radio operation, the dehors a checkbox one, and the tree still takes both with "Aprire
  l'attività"). The unrouted combinations are therefore real combined pratiche: each needs its own crawl, steps file and run.
- Every section these combinations show is in `dictionary/fnsuap.yaml` **except the fire prevention's**: the six
  `SCIA VV.F. - ...` sections and the professional's `ASSEVERAZIONE DEL PROFESSIONISTA AI FINI DELLA SICUREZZA ANTINCENDIO`
  and `DISTINTA DELLA DOCUMENTAZIONE TECNICA ALLEGATA`. They are unread (no crawl has them). So the combinations
  without a PIN need crawls and runs; those with a PIN also need the VV.F. sections read, and the asseverazione is a
  technician's document.
- The probe records section names only: the combined pratica's boxes come from a crawl of the combination (`catalogue.py
  ops ... --combo`), never from joining two operations' lists.

`wizard.js` `pairs` now takes a sector per pair (`a.sector`), as the SUAP's pairs need; the SUE's name none and use
`opts.sector` as before.
