#!/usr/bin/env python3
"""A made-up dossier in the documents' real formats: what an architect would hand over for the
CILA rehearsal's P6 case (rehearsals/cila-fittizia/dossier-p6.md, fixture-p6.json).

  dossier.py OUT_DIR

No real document of these kinds is public (a visura, a lease, a deed carry someone's data), so
each is written from its published layout: the visura from the Agenzia delle Entrate's guide
"La visura catastale" (November 2025; its specimens are images, so the words and their order
are copied, not the bytes), the lease from the DM 16/01/2017 model's headings, the deed's
menzioni urbanistiche from art. 46 DPR 380/2001 and art. 40 L. 47/1985, the receipts from the
SUE's Costi page. Text in two columns where the real one has two, compressed as real PDFs are;
the identity card is a scan (no text), as it usually is. Everything is made up.
"""

import sys
import zlib
from pathlib import Path


def pdf(pages, pdfa=False):
    """A PDF of text pages: each page a list of (x, y, size, text), Helvetica, WinAnsi, its
    content compressed. A page given as None is a scan: a drawing and no text."""
    objs = []

    def add(body):
        objs.append(body)
        return len(objs)
    font = add(b"<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica /Encoding /WinAnsiEncoding >>")
    kids = []
    pages_id = len(objs) + 1 + 2 * len(pages)  # after every page and content
    for page in pages:
        if page is None:
            ops = b"0.6 g 60 300 470 300 re f 0.2 g 80 520 120 60 re f"
        else:
            lines = []
            for x, y, size, text in page:
                s = text.encode("cp1252").replace(b"\\", b"\\\\").replace(b"(", b"\\(").replace(b")", b"\\)")
                lines.append(b"BT /F1 %d Tf %d %d Td (%s) Tj ET" % (size, x, y, s))
            ops = b"\n".join(lines)
        data = zlib.compress(ops)
        content = add(b"<< /Length %d /Filter /FlateDecode >>\nstream\n" % len(data) + data + b"\nendstream")
        kids.append(add(b"<< /Type /Page /Parent %d 0 R /MediaBox [0 0 595 842] /Contents %d 0 R "
                        b"/Resources << /Font << /F1 %d 0 R >> >> >>" % (pages_id, content, font)))
    assert add(b"<< /Type /Pages /Kids [%s] /Count %d >>" % (b" ".join(b"%d 0 R" % k for k in kids), len(kids))) == pages_id
    meta = ""
    if pdfa:  # declared as an export to PDF/A writes it, unfiltered
        xmp = (b'<x:xmpmeta xmlns:x="adobe:ns:meta/"><rdf:RDF xmlns:rdf="http://www.w3.org/1999/02/22-rdf-syntax-ns#">'
               b'<rdf:Description xmlns:pdfaid="http://www.aiim.org/pdfa/ns/id/" pdfaid:part="2" pdfaid:conformance="B"/>'
               b'</rdf:RDF></x:xmpmeta>')
        meta = " /Metadata %d 0 R" % add(b"<< /Type /Metadata /Subtype /XML /Length %d >>\nstream\n" % len(xmp)
                                       + xmp + b"\nendstream")
    catalog = add(b"<< /Type /Catalog /Pages %d 0 R%s >>" % (pages_id, meta.encode()))
    out, offsets = bytearray(b"%PDF-1.7\n%\xe2\xe3\xcf\xd3\n"), []
    for i, body in enumerate(objs, 1):
        offsets.append(len(out))
        out += b"%d 0 obj\n" % i + body + b"\nendobj\n"
    xref = len(out)
    out += b"xref\n0 %d\n0000000000 65535 f \n" % (len(objs) + 1)
    out += b"".join(b"%010d 00000 n \n" % o for o in offsets)
    out += b"trailer\n<< /Size %d /Root %d 0 R >>\nstartxref\n%d\n%%%%EOF\n" % (len(objs) + 1, catalog, xref)
    return bytes(out)


def column(x, y, lines, size=9, step=13):
    """Lines one under another from (x, y)."""
    return [(x, y - i * step, size, t) for i, t in enumerate(lines)]


def visura():
    """A visura attuale per immobile, as the AdE guide's specimens lay it out: the left column
    the data, the right the act each comes from."""
    head = [(50, 790, 10, "Agenzia delle Entrate"), (50, 770, 9, "Ufficio Provinciale di Napoli - Territorio"),
            (50, 758, 9, "Servizi Catastali"), (380, 782, 9, "Data: 30/10/2026"), (380, 770, 9, "Ora: 10:14:08"),
            (380, 758, 9, "Numero Pratica: T000417/2026"), (380, 746, 9, "Pag: 1 - Segue")]
    page1 = head + [
        (180, 715, 14, "Visura attuale per immobile"),
        (160, 698, 10, "Situazione degli atti informatizzati al 30/10/2026"),
        (50, 670, 9, "Dati della richiesta"),
        (50, 658, 9, "Comune di NAPOLI (Codice:F839)"),
        (50, 646, 9, "Provincia di NAPOLI"),
        (50, 634, 9, "Catasto Fabbricati Sez. Urb.: AVV Foglio: 12 Particella: 345 Sub.: 7"),
        (50, 600, 10, "Immobile di catasto fabbricati - n.1"), (330, 600, 10, "Causali di aggiornamento ed annotazioni"),
        (50, 576, 10, "Dati identificativi"),
        *column(60, 560, ["Comune di NAPOLI (F839) (NA)", "Sezione Urbana AVV Foglio 12 Particella 345 Subalterno 7",
                          "Partita: 1043221"]),
        (330, 560, 9, "Impianto meccanografico del 30/06/1987"),
        (50, 506, 10, "Indirizzo"),
        (60, 490, 9, "VIA DOMENICO FONTANA n. 40 Scala B Piano 3"),
        (330, 490, 9, "Impianto meccanografico del 30/06/1987"),
        (50, 460, 10, "Dati di classamento"),
        *column(60, 444, ["Rendita: Euro 852,15", "Rendita: Lire 1.650.000", "Zona censuaria 3,",
                          "Categoria A/2a), Classe 4, Consistenza 5,5 vani"]),
        (330, 444, 9, "Variazione del 01/01/1992 Variazione del quadro tariffario"),
    ]
    page2 = [*head[:3], (380, 782, 9, "Data: 30/10/2026"), (380, 746, 9, "Pag: 2 - Fine"),
             (50, 715, 10, "Dati di superficie"),
             *column(60, 699, ["Totale: 98 m2", "Totale escluse aree scoperte b): 95 m2"]),
             *column(330, 699, ["Superficie di impianto pubblicata il 09/11/2015",
                                "Dati relativi alla planimetria: data di presentazione",
                                "18/05/1962, prot. n. 4521"]),
             (50, 640, 10, "Intestazione attuale dell'immobile n. 1 - totale intestati: 1"),
             *column(60, 616, ["IMMOBILIARE FITTIZIA S.R.L.", "Sede in NAPOLI (NA)", "(CF 81764350633)",
                               "Diritto di: Proprieta' per 1/1 deriva dall'atto 1)"]),
             *column(330, 616, ["1. Atto del 14/02/2003 Pubblico ufficiale ESEMPIO MARIO", "Sede NAPOLI (NA)",
                                "Repertorio n. 41257 - COMPRAVENDITA", "Nota presentata con Modello Unico n. 3121.1/2003"]),
             (60, 540, 9, "Visura telematica"),
             *column(60, 120, ["Legenda", "a) A/2: Abitazioni di tipo civile",
                               "b) Escluse le superfici di balconi, terrazzi e aree scoperte pertinenziali e accessorie"],
                     size=8, step=11)]
    return pdf([page1, page2])


def lease():
    return pdf([column(60, 790, [
        "CONTRATTO DI LOCAZIONE AD USO ABITATIVO",
        "(Legge 9 dicembre 1998, n. 431, articolo 2, comma 1)",
        "",
        "La IMMOBILIARE FITTIZIA S.R.L., con sede in Napoli, Via Toledo 256, C.F. e P.IVA 81764350633,",
        "in persona della legale rappresentante Giulia Esempio, di seguito denominata LOCATORE,",
        "concede in locazione a",
        "Luca Fittizio, nato a Napoli il 02/07/1991, C.F. FTTLCU91L02F839F, di seguito denominato CONDUTTORE,",
        "che accetta, l'unita' immobiliare posta in Napoli, Via Domenico Fontana n. 40, scala B, piano 3,",
        "interno 7, CAP 80128, composta di 4 vani oltre accessori,",
        "censita al Catasto Fabbricati del Comune di Napoli, Sez. Urb. AVV, foglio 12, particella 345,",
        "subalterno 7, categoria A/2, classe 4, rendita catastale Euro 852,15.",
        "",
        "Art. 1 (Durata) Il contratto e' stipulato per la durata di anni 4, dal 01/03/2024 al 28/02/2028.",
        "Art. 2 (Canone) Il canone annuo di locazione e' convenuto in euro 9.600,00.",
        "Art. 9 (Modifiche) Il conduttore non puo' apportare modifiche all'immobile senza il consenso",
        "scritto del locatore.",
        "",
        "Napoli, 20/02/2024",
        "Il Locatore                                Il Conduttore",
    ])])


def deed():
    """The owner's deed: the menzioni urbanistiche name the titles the building was built under."""
    return pdf([column(60, 790, [
        "Repertorio n. 41257                                        Raccolta n. 15820",
        "COMPRAVENDITA",
        "REPUBBLICA ITALIANA",
        "L'anno duemilatre, il giorno quattordici del mese di febbraio, in Napoli, innanzi a me",
        "dottor Mario Esempio, Notaio in Napoli, sono presenti: ... (omissis)",
        "Articolo 1 - Oggetto. La parte venditrice vende alla IMMOBILIARE FITTIZIA S.R.L., che acquista,",
        "l'appartamento in Napoli, Via Domenico Fontana n. 40, scala B, piano terzo, interno 7, riportato",
        "nel Catasto Fabbricati del Comune di Napoli alla Sezione AVV, foglio 12, particella 345, sub. 7.",
        "Articolo 5 - Menzioni urbanistiche. Ai sensi dell'art. 40 della legge 28 febbraio 1985 n. 47",
        "e dell'art. 46 del D.P.R. 6 giugno 2001 n. 380, la parte venditrice dichiara che il fabbricato",
        "di cui fa parte quanto in oggetto e' stato edificato in forza della licenza edilizia n. 1234",
        "rilasciata dal Comune di Napoli in data 12/03/1960, e successiva variante, licenza edilizia",
        "n. 567 del 05/06/1961, e che successivamente non sono state eseguite opere per le quali",
        "fosse necessario alcun titolo abilitativo.",
        "Articolo 6 - Conformita' catastale. La parte venditrice dichiara che i dati catastali e la",
        "planimetria depositata in catasto sono conformi allo stato di fatto.",
    ])])


def relazione_lines():
    return [
        "Studio Fittizio - arch. Chiara Fittizia",
        "RELAZIONE TECNICA ILLUSTRATIVA",
        "(art. 6-bis, comma 5, D.P.R. 380/2001 - C.I.L.A. presentata a lavori in corso)",
        "",
        "OGGETTO: Manutenzione straordinaria non strutturale in appartamento: demolizione e ricostruzione",
        "di due tramezzi interni con nuova distribuzione di cucina e bagno, nuovo bagno, rifacimento degli",
        "impianti idrico ed elettrico.",
        "UBICAZIONE: Napoli, Via Domenico Fontana 40, scala B, piano 3, interno 7.",
        "",
        "1. DESCRIZIONE DELL'INTERVENTO",
        "Demolizione e ricostruzione di due tramezzi interni con nuova distribuzione di cucina e bagno;",
        "nuovo bagno; rifacimento degli impianti idrico ed elettrico della cucina e del bagno. Opere",
        "interne non strutturali, senza modifiche di volume, superficie o destinazione d'uso.",
        "",
        "2. QUALIFICAZIONE DELL'INTERVENTO",
        "L'intervento rientra nella manutenzione straordinaria di cui all'art. 3, comma 1, lettera b),",
        "del D.P.R. 380/2001. Le opere non interessano le parti strutturali dell'edificio e non",
        "modificano i prospetti. Non comportano mutamento della destinazione d'uso ne' aumento del",
        "carico urbanistico: l'intervento e' a titolo gratuito.",
        "",
        "3. INQUADRAMENTO URBANISTICO E VINCOLI",
        "L'immobile ricade in zona B - agglomerati urbani di recente formazione della Variante",
        "generale al PRG. L'immobile non e' sottoposto a vincolo paesaggistico ne' a tutela ai sensi",
        "della Parte II del D.Lgs. 42/2004. Le opere non interessano parti comuni dell'edificio.",
        "",
        "4. STATO DEI LAVORI",
        "I lavori sono iniziati in data 19/10/2026 e sono tuttora in corso.",
        "",
        "5. SICUREZZA",
        "Operano in cantiere due imprese esecutrici; l'entita' presunta del cantiere e' inferiore a",
        "200 uomini-giorno. La notifica preliminare (art. 99 D.Lgs. 81/2008) e' stata trasmessa.",
        "",
        "6. ALTRE INFORMAZIONI",
        "Non si dichiarano tolleranze costruttive (art. 34-bis D.P.R. 380/2001). Non sono necessari",
        "altri atti di assenso. Non sono incaricati altri tecnici. Direttore dei lavori: il sottoscritto",
        "progettista.",
        "",
        "Napoli, 28/10/2026                              Il tecnico, arch. Chiara Fittizia",
    ]


def relazione():
    return pdf([column(60, 790, relazione_lines())], pdfa=True)


def one_page(lines, pdfa=False):
    return pdf([column(60, 790, lines)], pdfa=pdfa)


DOCUMENTS = {
    "Visura_attuale_immobile.pdf": visura,
    "Contratto_di_locazione.pdf": lease,
    "Atto_compravendita_2003.pdf": deed,
    "Relazione_tecnica.pdf": relazione,
    "Assenso_proprietario.pdf": lambda: one_page([
        "Spett.le arch. Chiara Fittizia", "Napoli, 24/10/2026", "",
        "OGGETTO: Assenso del proprietario all'esecuzione dei lavori - Via Domenico Fontana 40, int. 7",
        "La sottoscritta Giulia Esempio, legale rappresentante della IMMOBILIARE FITTIZIA S.R.L.,",
        "proprietaria dell'unita' immobiliare, dichiara di prestare il proprio assenso all'esecuzione",
        "dei lavori di manutenzione straordinaria descritti nella C.I.L.A. presentata dal conduttore",
        "Luca Fittizio.", "", "In fede"]),
    "Notifica_preliminare.pdf": lambda: one_page([
        "NOTIFICA PRELIMINARE (art. 99 del D.Lgs. 81/2008)", "",
        "1. Data della comunicazione: 17/10/2026",
        "2. Indirizzo del cantiere: Napoli, Via Domenico Fontana 40, interno 7",
        "3. Committente: Luca Fittizio",
        "4. Natura dell'opera: manutenzione straordinaria non strutturale",
        "8. Data presunta d'inizio dei lavori: 19/10/2026",
        "10. Numero massimo presunto dei lavoratori sul cantiere: 4",
        "11. Numero previsto di imprese e di lavoratori autonomi sul cantiere: 2",
        "12. Identificazione delle imprese gia' selezionate: Edil Fittizia di Marco Esempio;",
        "    Impianti Fittizi S.n.c."]),
    "Elaborati_grafici.pdf": lambda: one_page([
        "Tavola 01 - Inquadramento: stralcio PRG, planimetria catastale",
        "Tavola 02 - Stato di fatto - pianta piano terzo, scala 1:50",
        "Tavola 03 - Stato di progetto - pianta piano terzo, scala 1:50",
        "Tavola 04 - Stato comparativo (demolizioni in giallo, costruzioni in rosso), scala 1:50"], pdfa=True),
    "Documentazione_fotografica.pdf": lambda: one_page([
        "DOCUMENTAZIONE FOTOGRAFICA", "Foto 1 - Cucina, stato attuale (cono ottico 1)",
        "Foto 2 - Bagno, stato attuale (cono ottico 2)", "Planimetria con i coni ottici"], pdfa=True),
    "Ricevuta_diritti.pdf": lambda: one_page([
        "Poste Italiane - BancoPosta", "RICEVUTA DI VERSAMENTO - Bollettino",
        "sul C/C n. 57060964 intestato a COMUNE DI NAPOLI SERVIZIO TESORERIA EDILIZIA PRIVATA",
        "Importo: Euro 151,00",
        "Causale: N1051_SUE - Fittizio Luca - Via Domenico Fontana 40", "Data: 28/10/2026"]),
    "Ricevuta_sanzione.pdf": lambda: one_page([
        "Banca Fittizia - Disposizione di bonifico SEPA eseguita",
        "Beneficiario: COMUNE DI NAPOLI", "IBAN: IT95X0306903496100000046118", "Importo: EUR 333,00",
        "Causale: N1051_SUE - sanzione CILA tardiva art. 6-bis c. 5 - Fittizio Luca - Via Domenico Fontana 40",
        "Data esecuzione: 28/10/2026"]),
    "Documento_identita_Luca.pdf": lambda: pdf([None]),  # a scan: no text
    # Napoli's annexes (DD 603/2025), as the Comune's own models head them.
    "Allegato_A_Programma_100.pdf": lambda: one_page([
        "Allegato A - Nuovo Programma 100", "DICHIARAZIONE SOSTITUTIVA DELL'ATTO DI NOTORIETA'",
        "(art. 47 D.P.R. 28 dicembre 2000 n. 445)",
        "Il sottoscritto dichiara di non avere debiti nei confronti del Comune di Napoli per le entrate",
        "oggetto della verifica tributaria, e che non sono in corso procedure di riscossione coattiva."]),
    "Modello_DP.pdf": lambda: one_page([
        "Modello DP - Dichiarazione di pagamento", "ai sensi della Legge regionale Campania n. 59/2018",
        "Il sottoscritto professionista dichiara di aver ricevuto dal committente il pagamento delle",
        "spettanze relative agli elaborati progettuali della pratica edilizia."]),
}


def write(out):
    out = Path(out)
    out.mkdir(parents=True, exist_ok=True)
    for name, make in DOCUMENTS.items():
        (out / name).write_bytes(make())
    return out


if __name__ == "__main__":
    print(write(sys.argv[1] if len(sys.argv) > 1 else "dossier-p6"))
