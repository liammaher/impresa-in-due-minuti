<h1 align="center">Portali</h1>

<p align="center">Le pratiche dei portali della pubblica amministrazione, preparate da Claude. Per ora: il SUE del Comune di Napoli. Gratuito e open source.</p>

Portali prepara una pratica del SUE del Comune di Napoli (CILA, SCIA, permesso di costruire e le
altre), su impresainungiorno, dai documenti del Suo cliente. Si ferma dove comincia la Sua parte:
l'accesso con SPID, le dichiarazioni, la firma digitale, il pagamento e l'invio. Claude non spunta mai
una dichiarazione, non firma, non paga e non invia.

## Lo provi in pochi minuti

Dopo l'installazione scriva **«Fammi vedere una prova»**. Claude compila sul portale vero una CILA di
prova, con committente, studio e documenti inventati, senza farLe domande: Lei accede con SPID, e in
un paio di minuti vede sul portale la bozza «PROVA NON INVIARE - CILA di prova» compilata. Poi la
cancelli da «Pratiche in bozza». Anche su un Suo caso, se non ha ancora i documenti, basta dire «è una
prova, inventa i dati».

## Installazione

La guida passo passo, da mandare a un collega: **https://liammaher.github.io/portali/**

Nell'app Claude per computer, senza terminale:

1. Apra **Personalizzazione** (Customize) e la scheda **Plugin**.
2. Clicchi **Aggiungi** (Add), poi **Aggiungi marketplace** (Add marketplace) e **Aggiungi da un repository**
   (Add from a repository), scriva `liammaher/portali` nella casella, lo scelga nell'elenco sotto e
   clicchi **Sincronizza** (Sync).
3. Apra Portali, tra i **Nuovi plugin**, e clicchi **Aggiungi** (Add).
4. Per aggiornarlo (Portali cambia quando cambia il portale): **Aggiungi** → **Gestisci marketplace**
   (Manage marketplaces) → **⋯** accanto a portali → **Verifica aggiornamenti** (Check for updates).
   Lo faccia ogni tanto e prima di una pratica importante. Un avviso che propone **Concedi accesso** a
   GitHub lo può chiudere: non serve.

Tra parentesi i nomi dell'app in inglese. In uno studio con piano Team o Enterprise basta che lo
aggiunga l'amministratore: arriva a tutti. Se dopo **Verifica aggiornamenti** vede ancora una versione
vecchia, rimuova il marketplace (**Rimuovi**, stesso menu), chiuda e riapra l'app e lo aggiunga di nuovo
(punto 2).

Poi apra nell'app la cartella dei Suoi lavori, con una sottocartella per ogni lavoro. I dati dello
studio li chiede Claude alla prima pratica, una volta sola. Serve Python 3 sul computer: su un Mac che
non lo ha, alla prima pratica macOS propone di installare gli strumenti per sviluppatori di Apple, che
lo contengono; accetti. Su Windows lo installi da python.org.

## Come va un lavoro

1. Metta i documenti del lavoro nella sua cartella: visura, atto o contratto, documento d'identità,
   relazione tecnica, elaborati.
2. Scriva una riga: «CILA per il signor Bianchi, i documenti sono nella cartella Bianchi».
3. Claude risponde con un solo messaggio: se la pratica è coperta, cosa dicono i documenti, quale
   pratica propone, le poche domande. Risponda una volta.
4. Acceda con SPID nel browser dell'app e scriva a Claude «fatto». Claude compila la bozza sul portale
   (non tocchi la pagina finché non Le scrive), poi confronta l'anteprima del portale con i documenti.
5. Quando la bozza è pronta, Claude Le scrive in poche righe cosa controllare e cosa resta a Lei sul
   portale: l'anteprima, le dichiarazioni, la firma, il pagamento e l'invio.
6. Dopo l'invio, Claude Le dice le prossime scadenze e la pratica che di solito segue.

## Cosa copre, e cosa no

- **Per ora il SUE del Comune di Napoli**, su impresainungiorno; altri sportelli (il SUAP) e altri
  comuni si aggiungono nel tempo, nello stesso plugin. Oggi una pratica del SUAP (un negozio, un
  ristorante), un immobile in un altro comune, un altro ente (Genio Civile, Soprintendenza, ASL,
  Catasto, Agenzia delle Entrate, Regione) o una pratica che Portali non conosce: Claude Le dice
  subito che non è coperta, e non apre nulla.
- Per ogni lavoro Claude Le dice prima se la pratica è **coperta** (la prepara per intero), se ha
  **solo indicazioni** (non la compila) o se **non è coperta**, e perché. Poi Lei conferma, e solo
  allora si comincia.
- **Coperta** vuol dire: compilata sul portale vero con dati di prova, rileggendo ogni valore. Nessuna
  pratica reale è ancora stata inviata con Portali.
- Le regole vengono dalla biblioteca [pratiche-napoli](https://github.com/liammaher/pratiche-napoli),
  ogni fatto con la sua fonte. Ciò che la biblioteca non copre, Claude lo dice.

## Dove vanno i dati dei Suoi clienti

Nella cartella dei Suoi lavori su questo computer, nella conversazione con Claude e sul portale.
Portali non ha un server suo.

**Claude legge i documenti del lavoro**, compila la bozza e la confronta con essi: i dati dei clienti
(nomi, codici fiscali, indirizzi, dati catastali) passano quindi dalla conversazione con Claude, come
ogni documento che Lei vi apre. Claude glielo dice alla prima pratica. Se un cliente non vuole che i
suoi documenti passino da Claude, non usi Portali per quel lavoro. Password, PIN e accesso SPID
mai: l'accesso al portale lo fa Lei.

Lei è titolare del trattamento dei dati dei Suoi clienti. In Claude disattivi «Aiuta a migliorare
Claude» (Impostazioni → Privacy) e usi il browser dell'app, non Claude in Chrome.

## Prima di usarlo

- Portali **non è uno strumento ufficiale**: non è affiliato al Comune di Napoli, a InfoCamere né ad
  altri enti, e non è una consulenza legale ([NOTICE.md](NOTICE.md)).
- Legga l'[uso responsabile](docs/responsible-use.md). In breve: Lei firma e risponde della pratica;
  una pratica alla volta, con il Suo SPID; nessun dato personale in una segnalazione.
- Per chiedere una pratica o segnalare un portale cambiato apra una
  [segnalazione](https://github.com/liammaher/portali/issues/new/choose); come contribuire è in
  [CONTRIBUTING.md](CONTRIBUTING.md). Se qualcosa di Portali non funziona, lo dica a Claude: Le
  prepara la segnalazione già compilata, senza i dati dei clienti, e Lei la rilegge prima di inviarla.

Per collegarlo agli altri strumenti dello studio, usarlo su molti lavori insieme o automatizzare altro,
scriva a liampmaher1996@gmail.com.

## Per sviluppatori

- **Il plugin**: [plugin/README.md](plugin/README.md) (come si costruisce) e
  [plugin/portali/README.md](plugin/portali/README.md) (il testo che il tecnico legge
  nell'app, da tenere allineato con questa pagina). Installazione e aggiornamenti:
  [docs/install.md](docs/install.md); dove va il progetto: [docs/north-star.md](docs/north-star.md).
- **Il compilatore del portale**: [claude/skills/pratica/portal/README.md](claude/skills/pratica/portal/README.md).
- **pvault**, l'archivio cifrato locale che il plugin di oggi non contiene (`plugin/build.yaml`
  `vault: false`): [docs/pvault.md](docs/pvault.md).

Build dai sorgenti e test (Go 1.26+; Python della venv del compilatore, `~/.cache/pratica-portal/venv`):

```sh
make build                       # bin/pvault (+ bin/pvault-touchid su macOS)
make test                        # test Go con -race
(cd mcp && npx tsc -p tsconfig.test.json && npm test)
~/.cache/pratica-portal/venv/bin/python plugin/build.py --library ../pratiche-napoli --out /tmp/portali
~/.cache/pratica-portal/venv/bin/python plugin/test_build.py
```

## Licenza

MIT, vedi [LICENSE](LICENSE). Fork di [lovincyrus/personal-vault](https://github.com/lovincyrus/personal-vault)
© Cyrus Goh; le estensioni italiane e le modifiche di sicurezza © Liam Maher. Il materiale di terzi è in
[NOTICE.md](NOTICE.md).
