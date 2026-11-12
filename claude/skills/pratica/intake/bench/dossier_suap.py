#!/usr/bin/env python3
"""A made-up dossier for a business's pratica (the SUAP): what a tecnico would hand over to open a shop, or to take over a bar.

  dossier_suap.py OUT_DIR [negozio|bar]

THE DOCUMENTS ARE MADE UP. No real visura camerale, commercial lease or relazione descrittiva is public (they carry a
business's and a person's data), and the 2026-11-12 sample was never checked against a real one: the visura camerale
follows the headings of the Camera di Commercio's «visura ordinaria» (Dati anagrafici, Informazioni sulla sede, Attività,
Persone con cariche) as the maintainer remembers them, one label and value per line; the lease follows the headings of an
«uso diverso dall'abitativo» contract (art. 27 L. 392/1978); the catastal visura is dossier.py's, with a shop's data; the
relazione descrittiva dei locali is worded as a tecnico would write it (nobody publishes one). A real one may lay its
text out otherwise: the first real visura camerale is the test that counts. Everything is made up: the names, the
codici fiscali (check letters valid), the numbers.

`negozio` is rehearsals/negozio-fittizio's case (fixture.json): a ditta individuale opening a stationery shop. `bar` is a
srl with two administrators taking over a bar by renting a business: ATECO 56.30.00, consumption on the spot, a sign.
File names carry no name: a real folder's might, and intake.json lists them.
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from dossier import column, one_page, pdf  # noqa: E402


def camerale(case):
    if case == "negozio":
        lines = [
            "CAMERA DI COMMERCIO INDUSTRIA ARTIGIANATO E AGRICOLTURA DI NAPOLI",
            "VISURA ORDINARIA - Estratto dal Registro delle Imprese", "Data: 06/11/2026", "",
            "DATI ANAGRAFICI IMPRESA",
            "Denominazione: BOTTEGA FITTIZIA DI CARMELA FITTIZIA",
            "Indirizzo Sede legale: NAPOLI (NA) VIA LUCA GIORDANO 50 CAP 80127",
            "Indirizzo PEC: bottega.fittizia@pec.example.it",
            "Numero REA: NA - 1234567",
            "Codice fiscale: FTTCML88C61F839H",
            "Partita IVA: 55501230639",
            "Forma giuridica: IMPRESA INDIVIDUALE",
            "Data iscrizione: 03/11/2026",
            "Data di inizio dell'attivita: 02/11/2026", "",
            "ATTIVITA, ALBI ELENCHI E LICENZE",
            "Codice ATECO: 47.62.20 (attivita prevalente)",
            "Attivita esercitata: Cartoleria e articoli da regalo, vendita al dettaglio, senza alimenti", "",
            "PERSONE CON CARICHE O QUALIFICHE",
            "TITOLARE FIRMATARIO: FITTIZIA CARMELA",
            "Nata a: NAPOLI (NA) il 21/03/1988",
            "Codice fiscale: FTTCML88C61F839H",
            "Residente in: NAPOLI (NA) VIA DOMENICO CIMAROSA 30 CAP 80127",
            "Data inizio carica: 02/11/2026"]
    else:
        lines = [
            "CAMERA DI COMMERCIO INDUSTRIA ARTIGIANATO E AGRICOLTURA DI NAPOLI",
            "VISURA ORDINARIA - Estratto dal Registro delle Imprese", "Data: 06/11/2026", "",
            "DATI ANAGRAFICI IMPRESA",
            "Denominazione: CAFFE DEL MOLO FITTIZIO S.R.L.",
            "Indirizzo Sede legale: NAPOLI (NA) VIA CARACCIOLO 12 CAP 80122",
            "Indirizzo PEC: caffedelmolo@pec.example.it",
            "Numero REA: NA - 7654321",
            "Codice fiscale: 09876540633",
            "Partita IVA: 09876540633",
            "Forma giuridica: SOCIETA A RESPONSABILITA LIMITATA",
            "Data atto di costituzione: 10/09/2026",
            "Data iscrizione: 14/09/2026",
            "Data di inizio dell'attivita: 14/09/2026", "",
            "ATTIVITA, ALBI ELENCHI E LICENZE",
            "Codice ATECO: 56.30.00 (attivita prevalente)",
            "Attivita esercitata: Bar, caffetteria e somministrazione di alimenti e bevande", "",
            "PERSONE CON CARICHE O QUALIFICHE",
            "AMMINISTRATORE UNICO: ESEMPIO GIULIA",
            "Nata a: NAPOLI (NA) il 30/11/1970",
            "Codice fiscale: SMPGLI70S70F839A",
            "Residente in: NAPOLI (NA) VIA TOLEDO 256 CAP 80134",
            "Data inizio carica: 10/09/2026",
            "SOCIO AMMINISTRATORE: FITTIZIO MARCO",
            "Nato a: NAPOLI (NA) il 02/05/1975",
            "Codice fiscale: FTTMRC75E02F839F",
            "Residente in: NAPOLI (NA) VIA FORIA 100 CAP 80139",
            "Data inizio carica: 10/09/2026"]
    return one_page(lines)


def visura_locale(case):
    """The Agenzia's visura attuale per immobile, as dossier.visura lays it out, for the business's premises."""
    foglio, part, sub, via, civ, cat, mq = ((14, 233, 7, "VIA LUCA GIORDANO", 50, "C/1", 45) if case == "negozio"
                                           else (21, 118, 3, "VIA CARACCIOLO", 12, "C/1", 70))
    head = [(50, 790, 10, "Agenzia delle Entrate"), (50, 770, 9, "Ufficio Provinciale di Napoli - Territorio"),
            (50, 758, 9, "Servizi Catastali"), (380, 782, 9, "Data: 30/10/2026"), (380, 770, 9, "Ora: 10:14:08"),
            (380, 758, 9, "Numero Pratica: T000518/2026"), (380, 746, 9, "Pag: 1 - Segue")]
    page1 = head + [
        (180, 715, 14, "Visura attuale per immobile"),
        (160, 698, 10, "Situazione degli atti informatizzati al 30/10/2026"),
        (50, 670, 9, "Dati della richiesta"), (50, 658, 9, "Comune di NAPOLI (Codice:F839)"),
        (50, 646, 9, "Provincia di NAPOLI"),
        (50, 634, 9, f"Catasto Fabbricati Foglio: {foglio} Particella: {part} Sub.: {sub}"),
        (50, 600, 10, "Immobile di catasto fabbricati - n.1"), (330, 600, 10, "Causali di aggiornamento ed annotazioni"),
        (50, 576, 10, "Dati identificativi"),
        *column(60, 560, ["Comune di NAPOLI (F839) (NA)", f"Foglio {foglio} Particella {part} Subalterno {sub}", "Partita: 1043888"]),
        (330, 560, 9, "Impianto meccanografico del 30/06/1987"),
        (50, 506, 10, "Indirizzo"), (60, 490, 9, f"{via} n. {civ} Piano T"),
        (50, 460, 10, "Dati di classamento"),
        *column(60, 444, ["Rendita: Euro 1.020,00", "Zona censuaria 3,", f"Categoria {cat}a), Classe 7, Consistenza {mq} m2"])]
    page2 = [*head[:3], (380, 746, 9, "Pag: 2 - Fine"),
             (50, 715, 10, "Dati di superficie"), *column(60, 699, [f"Totale: {mq} m2"]),
             *column(330, 699, ["Dati relativi alla planimetria: data di presentazione", "05/03/1989, prot. n. 2231"]),
             (50, 640, 10, "Intestazione attuale dell'immobile n. 1 - totale intestati: 1"),
             *column(60, 616, ["IMMOBILIARE FITTIZIA S.R.L.", "Sede in NAPOLI (NA)", "(CF 81764350633)",
                               "Diritto di: Proprieta' per 1/1 deriva dall'atto 1)"]),
             (60, 540, 9, "Visura telematica")]
    return pdf([page1, page2])


def locazione(case):
    if case == "negozio":
        parties = ["La IMMOBILIARE FITTIZIA S.R.L., con sede in Napoli, Via Toledo 256, C.F. e P.IVA 81764350633,",
                   "in persona della legale rappresentante Giulia Esempio, di seguito denominata LOCATORE,",
                   "concede in locazione a", "BOTTEGA FITTIZIA DI CARMELA FITTIZIA, P.IVA 55501230639, in persona del titolare,",
                   "di seguito denominata CONDUTTORE, che accetta, l'unita' immobiliare ad uso negozio",
                   "posta in Napoli, Via Luca Giordano n. 50, piano terra, CAP 80127,",
                   "censita al Catasto Fabbricati, foglio 14, particella 233, subalterno 7, categoria C/1,",
                   "con superficie di 45 mq."]
        term = "Art. 1 (Durata) Il contratto e' stipulato per la durata di anni 6, dal 01/11/2026 al 31/10/2032."
    else:
        parties = ["La IMMOBILIARE FITTIZIA S.R.L., con sede in Napoli, Via Toledo 256, C.F. e P.IVA 81764350633,",
                   "in persona della legale rappresentante Giulia Esempio, di seguito denominata LOCATORE,",
                   "concede in locazione a", "CAFFE DEL MOLO FITTIZIO S.R.L., P.IVA 09876540633, in persona dell'amministratore,",
                   "di seguito denominata CONDUTTORE, che accetta, l'unita' immobiliare ad uso bar",
                   "posta in Napoli, Via Caracciolo n. 12, piano terra, CAP 80122,",
                   "censita al Catasto Fabbricati, foglio 21, particella 118, subalterno 3, categoria C/1,",
                   "con superficie di 70 mq."]
        term = "Art. 1 (Durata) Il contratto e' stipulato per la durata di anni 6, dal 15/09/2026 al 14/09/2032."
    return one_page(["CONTRATTO DI LOCAZIONE AD USO DIVERSO DALL'ABITATIVO", "(Legge 27 luglio 1978, n. 392, articolo 27)", "",
                     *parties, "", term, "Art. 2 (Canone) Il canone annuo e' convenuto in euro 14.400,00.", "",
                     "Napoli, 20/10/2026", "Il Locatore                                Il Conduttore"])


def relazione_locali(case):
    if case == "negozio":
        lines = ["RELAZIONE DESCRITTIVA DEI LOCALI", "",
                 "OGGETTO: Apertura di un negozio di vicinato non alimentare (cartoleria e articoli da regalo), vendita al dettaglio.", "",
                 "Il locale e' al piano terra, con ingresso diretto dalla strada e un servizio igienico per il pubblico.",
                 "La superficie di vendita e' di 40 mq, oltre a un piccolo deposito.",
                 "Non e' prevista alcuna insegna esterna ne' diffusione sonora.",
                 "Non verranno venduti alcolici e senza consumo sul posto di alcun prodotto."]
    else:
        lines = ["RELAZIONE DESCRITTIVA DEI LOCALI", "",
                 "OGGETTO: Subingresso nell'attivita di bar con somministrazione di alimenti e bevande.", "",
                 "Il locale e' al piano terra, con banco, sala con tavoli e due servizi igienici.",
                 "La superficie di somministrazione e' di 45 mq. Con consumo sul posto, servizio al banco e ai tavoli.",
                 "E' prevista un'insegna esterna luminosa gia' esistente. Si usa un impianto audio di sottofondo.",
                 "Si somministrano bevande alcoliche. Non sono previsti tavolini all'aperto.",
                 "L'attivita' non e' soggetta a controllo di prevenzione incendi."]
    return one_page(lines, pdfa=True)


def agibilita():
    return one_page(["CERTIFICATO DI AGIBILITA'", "", "Si certifica l'agibilita' dell'unita' immobiliare ad uso commerciale",
                     "Via Luca Giordano n. 50, piano terra - Certificato n. 4421/1989 del 12/05/1989.", ""])


def affitto_azienda():
    return one_page(["CONTRATTO DI AFFITTO D'AZIENDA", "Innanzi a me, notaio in Napoli, sono comparsi:",
                     "la ESEMPIO CAFFE S.N.C., cedente, e la CAFFE DEL MOLO FITTIZIO S.R.L., affittuaria.",
                     "L'affittante concede in affitto d'azienda l'esercizio di bar sito in Napoli, Via Caracciolo n. 12,",
                     "con l'avviamento, gli arredi e le attrezzature, per anni 3 dal 15/09/2026.", ""])


COMMON = {
    "Ricevuta_diritti.pdf": lambda c: one_page(["Ricevuta telematica pagoPA", "Ente creditore: COMUNE DI NAPOLI - SUAP",
                                                "Importo: Euro 100,00", "Causale: diritti di istruttoria SUAP", "Data: 06/11/2026"]),
    "Documento_identita_titolare.pdf": lambda c: pdf([None]),  # a scan: no text
}
DOCUMENTS = {"Visura_camerale.pdf": camerale, "Visura_catastale_locale.pdf": visura_locale,
             "Contratto_locazione_commerciale.pdf": locazione, "Relazione_descrittiva_locali.pdf": relazione_locali,
             "Certificato_agibilita.pdf": lambda c: agibilita(), **COMMON}


def write(out, case="negozio"):
    out = Path(out)
    out.mkdir(parents=True, exist_ok=True)
    docs = dict(DOCUMENTS)
    if case == "bar":
        docs["Atto_affitto_azienda.pdf"] = lambda c: affitto_azienda()
        docs.pop("Certificato_agibilita.pdf")
    for name, make in docs.items():
        (out / name).write_bytes(make(case))
    return out


if __name__ == "__main__":
    print(write(sys.argv[1] if len(sys.argv) > 1 else "dossier-suap", sys.argv[2] if len(sys.argv) > 2 else "negozio"))
