# Portale SUE

Prepara una pratica edilizia del SUE del Comune di Napoli, su impresainungiorno, dai documenti del Suo
cliente. Si ferma dove comincia la Sua parte: le dichiarazioni, la firma digitale, il pagamento e
l'invio: Claude non spunta mai una dichiarazione, non firma, non paga e non invia. Gratuito e
open source.

## Lo provi in pochi minuti

Dopo l'installazione scriva **«Fammi vedere una prova»**. Claude compila sul portale vero una CILA
di prova, con committente, studio e documenti inventati, senza farLe domande: Lei accede con SPID,
e in un paio di minuti vede la bozza «PROVA NON INVIARE - CILA di prova» compilata e la pagina di
riepilogo. Poi la cancelli da «Pratiche in bozza». Anche su un Suo caso, se non ha ancora i
documenti, basta dire «è una prova, inventa i dati».

## Cosa copre, e cosa no

- **Solo il SUE del Comune di Napoli (Campania)**, su impresainungiorno. Una pratica del SUAP (un
  negozio, un ristorante), un immobile in un altro comune, un altro ente (Genio Civile, Soprintendenza, ASL, Catasto, Agenzia
  delle Entrate, Regione) o una pratica che Portale SUE non conosce: Claude Le dice subito che non è
  coperta dall'automazione, e non apre nulla.
- Per ogni lavoro Claude Le dice prima se la pratica è **coperta dall'automazione** (la prepara per
  intero), se ha **solo indicazioni** (non la compila) o se **non è coperta**, e perché. Poi Lei
  conferma, e solo allora si comincia.
- **Coperta** vuol dire: compilata sul portale vero con dati di prova, rileggendo ogni valore.
  Nessuna pratica reale è ancora stata inviata con Portale SUE.
- Le regole vengono dalla biblioteca pratiche-napoli, ogni fatto con la sua fonte. Ciò che la
  biblioteca non copre, Claude lo dice.

## Installazione

Serve un piano Claude a pagamento (Pro, Max, Team o Enterprise). Nell'app Claude per
computer, senza terminale:

1. Apra **Customize** e la scheda **Plugins**.
2. Clicchi **Add**, poi **Add marketplace**, e scriva `liammaher/portale-sue`.
3. Trovi Portale SUE nell'elenco e clicchi **Install**.
4. Sul marketplace attivi **Sync automatically**: così riceve da solo ogni aggiornamento, anche
   quando il portale cambia e una pratica va rimappata.

I nomi dei menu sono quelli dell'app in inglese. In uno studio con piano Team o Enterprise basta che
lo aggiunga l'amministratore: arriva a tutti.

<!-- vault -->
Poi scriva «Configura Portale SUE»: Claude prepara il Suo archivio privato, cifrato, su questo
computer. Lì restano i dati Suoi, dello studio e dei clienti; Claude non li vede mai.
<!-- /vault -->
<!-- no-vault -->
Poi apra nell'app la cartella dei Suoi lavori, con una sottocartella per ogni lavoro. I dati dello
studio li chiede Claude alla prima pratica, una volta sola.
<!-- download -->
Non serve installare altro: se sul computer non c'è Python, alla prima pratica Portale SUE ne scarica
uno (circa 25 MB, verificato), una volta sola.
<!-- /download -->
<!-- no-download -->
Serve Python 3 sul computer: su un Mac che non lo ha, alla prima pratica macOS propone di
installare gli strumenti per sviluppatori di Apple, che lo contengono; accetti. Su Windows lo
installi da python.org.
<!-- /no-download -->
<!-- /no-vault -->

## Come si usa

1. Metta i documenti di ogni lavoro in una cartella, una per lavoro: visura, atto o contratto,
   documento d'identità, relazione tecnica, elaborati. Meglio non allegarli alla conversazione:
   se lo fa, Claude li copia nella cartella, o Le chiede di salvarli lì.
2. Scriva una riga: «CILA per il signor Bianchi, i documenti sono nella cartella Bianchi».
<!-- vault -->
3. Claude risponde con un solo messaggio: se la pratica è coperta, cosa dicono i documenti,
   quale pratica propone, le poche domande. Risponda una volta, confermi con Touch ID (o Windows
   Hello).
4. Acceda con SPID nel browser dell'app e scriva sul portale il codice che compare sullo schermo.
<!-- /vault -->
<!-- no-vault -->
3. Claude risponde con un solo messaggio: se la pratica è coperta, cosa dicono i documenti,
   quale pratica propone, le poche domande. Risponda una volta.
4. Acceda con SPID nel browser dell'app e scriva a Claude «fatto». Claude compila la bozza: non
   tocchi la pagina finché non Le scrive. Poi confronta l'anteprima del portale con i documenti.
<!-- /no-vault -->
5. Quando la bozza è pronta, legga la pagina di riepilogo: cosa resta da fare a Lei, ogni
   controllo fatto, ogni valore inserito.
6. Dopo l'invio, Claude Le dice le prossime scadenze e la pratica che di solito segue.

## Dove vanno i dati dei Suoi clienti

<!-- vault -->
Nel Suo archivio su questo computer e sul portale. Da nessun'altra parte: Portale SUE non ha un
server.
<!-- /vault -->
<!-- no-vault -->
Nella cartella dei Suoi lavori su questo computer, nella conversazione con Claude e sul portale.
Portale SUE non ha un server suo.
**Claude legge i documenti del lavoro**, compila la bozza e la confronta con essi: i dati dei
clienti (nomi, codici fiscali, indirizzi, dati catastali) passano quindi dalla conversazione con
Claude, come ogni documento che Lei vi apre. Claude glielo dice alla prima pratica. Se un cliente
non vuole che i suoi documenti passino da Claude, non usi Portale SUE per quel lavoro.
Password, PIN e accesso SPID mai: l'accesso al portale lo fa Lei.
<!-- /no-vault -->
Lei è titolare del trattamento dei dati dei Suoi clienti. In Claude disattivi «Aiuta a
migliorare Claude» (Impostazioni → Privacy) e usi il browser dell'app, non Claude in Chrome.

## Prima di usarlo

Legga l'[uso responsabile](https://github.com/liammaher/portale-sue/blob/main/docs/responsible-use.md).
In breve: Lei firma e risponde della pratica; una pratica alla volta, con il Suo SPID; nessun dato
personale in una segnalazione. Per chiedere una pratica o segnalare un portale cambiato apra una
[segnalazione](https://github.com/liammaher/portale-sue/issues/new/choose).
Se qualcosa di Portale SUE non funziona, lo dica a Claude: Le prepara la segnalazione già
compilata, senza i dati dei clienti, e Lei la rilegge prima di inviarla.

## Per qualcosa in più

Per collegarlo agli altri strumenti dello studio, usarlo su molti lavori insieme o automatizzare
altro, scriva a liampmaher1996@gmail.com.
