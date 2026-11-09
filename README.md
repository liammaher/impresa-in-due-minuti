# Impresa in un minuto

Prepara una pratica del SUE del Comune di Napoli, su impresainungiorno, dai documenti del Suo
cliente. Si ferma dove comincia la Sua parte: le dichiarazioni, la firma digitale, il pagamento e
l'invio: Claude non spunta mai una dichiarazione, non firma, non paga e non invia. Gratuito e
open source.

## Lo provi in pochi minuti

Dopo l'installazione scriva **«Fammi vedere una prova»**. Claude compila sul portale vero una CILA
di prova, con committente, studio e documenti inventati, senza farLe domande: Lei accede con SPID,
e in un paio di minuti vede sul portale la bozza «PROVA NON INVIARE - CILA di prova» compilata.
Poi la cancelli da «Pratiche in bozza». Anche su un Suo caso, se non ha ancora i
documenti, basta dire «è una prova, inventa i dati».

## Cosa copre, e cosa no

- **Per ora il SUE del Comune di Napoli**, su impresainungiorno; altri sportelli e comuni si aggiungono
  nel tempo.
  Una pratica del SUAP (un negozio, un ristorante) non è ancora coperta.
  Un immobile in un altro comune, un altro ente (Genio Civile, Soprintendenza, ASL, Catasto, Agenzia
  delle Entrate, Regione) o una pratica che Impresa in un minuto non conosce: Claude Le dice subito che non è
  coperta dall'automazione, e non apre nulla.
- Per ogni lavoro Claude Le dice prima se la pratica è **coperta dall'automazione** (la prepara per
  intero), se ha **solo indicazioni** (non la compila) o se **non è coperta**, e perché. Poi Lei
  conferma, e solo allora si comincia.
- **Coperta** vuol dire: compilata sul portale vero con dati di prova, rileggendo ogni valore.
  Nessuna pratica reale è ancora stata inviata con Impresa in un minuto.
- Le regole vengono dalla biblioteca pratiche-napoli, ogni fatto con la sua fonte. Ciò che la
  biblioteca non copre, Claude lo dice.

## Installazione

La guida passo passo, da mandare a un collega: **https://liammaher.github.io/impresa-in-un-minuto/**

Nell'app Claude per computer, senza terminale:

1. Apra **Personalizzazione** (Customize) e la scheda **Plugin**.
2. Clicchi **Aggiungi** (Add), poi **Aggiungi marketplace** (Add marketplace) e **Aggiungi da un repository**
   (Add from a repository), scriva `liammaher/impresa-in-un-minuto` nella casella, lo scelga nell'elenco sotto e
   clicchi **Sincronizza** (Sync).
3. Apra Impresa in un minuto, tra i **Nuovi plugin**, e clicchi **Aggiungi** (Add).
4. Per aggiornarlo (Impresa in un minuto cambia quando cambia il portale): **Aggiungi** → **Gestisci marketplace**
   (Manage marketplaces) → **⋯** accanto a impresa-in-un-minuto → **Verifica aggiornamenti** (Check for updates).
   Lo faccia ogni tanto e prima di una pratica importante. Un avviso che propone **Concedi accesso** a
   GitHub lo può chiudere: non serve.

Tra parentesi i nomi dell'app in inglese. In uno studio con piano Team o Enterprise basta che lo
aggiunga l'amministratore: arriva a tutti. Se dopo **Verifica aggiornamenti** vede ancora una versione
vecchia, rimuova il marketplace (**Rimuovi**, stesso menu), chiuda e riapra l'app e lo aggiunga di nuovo
(punto 2).

Poi apra nell'app la cartella dei Suoi lavori, con una sottocartella per ogni lavoro. I dati dello
studio li chiede Claude alla prima pratica, una volta sola.
Serve Python 3 sul computer: su un Mac che non lo ha, alla prima pratica macOS propone di
installare gli strumenti per sviluppatori di Apple, che lo contengono; accetti. Su Windows lo
installi da python.org.

## Come si usa

1. Metta i documenti di ogni lavoro in una cartella, una per lavoro: visura, atto o contratto,
   documento d'identità, relazione tecnica, elaborati. Meglio non allegarli alla conversazione:
   se lo fa, Claude li copia nella cartella, o Le chiede di salvarli lì.
2. Scriva una riga: «CILA per il signor Bianchi, i documenti sono nella cartella Bianchi».
3. Claude risponde con un solo messaggio: se la pratica è coperta, cosa dicono i documenti,
   quale pratica propone, le poche domande. Risponda una volta.
4. Acceda con SPID nel browser dell'app e scriva a Claude «fatto». Claude compila la bozza: non
   tocchi la pagina finché non Le scrive. Poi confronta l'anteprima del portale con i documenti.
5. Quando la bozza è pronta, Claude Le scrive in poche righe cosa controllare e cosa resta a Lei
   sul portale: l'anteprima, le dichiarazioni, la firma, il pagamento e l'invio.
6. Dopo l'invio, Claude Le dice le prossime scadenze e la pratica che di solito segue.

## Dove vanno i dati dei Suoi clienti

Nella cartella dei Suoi lavori su questo computer, nella conversazione con Claude e sul portale.
Impresa in un minuto non ha un server suo.
**Claude legge i documenti del lavoro**, compila la bozza e la confronta con essi: i dati dei
clienti (nomi, codici fiscali, indirizzi, dati catastali) passano quindi dalla conversazione con
Claude, come ogni documento che Lei vi apre. Claude glielo dice alla prima pratica. Se un cliente
non vuole che i suoi documenti passino da Claude, non usi Impresa in un minuto per quel lavoro.
Password, PIN e accesso SPID mai: l'accesso al portale lo fa Lei.
Lei è titolare del trattamento dei dati dei Suoi clienti. In Claude disattivi «Aiuta a
migliorare Claude» (Impostazioni → Privacy) e usi il browser dell'app, non Claude in Chrome.

## Prima di usarlo

Impresa in un minuto **non è uno strumento ufficiale**: non è affiliato al Comune di Napoli, a
InfoCamere (che gestisce impresainungiorno) né ad altri enti, e non è una consulenza legale. Il nome
gioca con quello del portale, ma è un progetto indipendente, gratuito e open source.

Legga l'[uso responsabile](https://github.com/liammaher/impresa-in-un-minuto/blob/main/docs/responsible-use.md).
In breve: Lei firma e risponde della pratica; una pratica alla volta, con il Suo SPID; nessun dato
personale in una segnalazione. Per chiedere una pratica o segnalare un portale cambiato apra una
[segnalazione](https://github.com/liammaher/impresa-in-un-minuto/issues/new/choose).
Se qualcosa di Impresa in un minuto non funziona, lo dica a Claude: Le prepara la segnalazione già
compilata, senza i dati dei clienti, e Lei la rilegge prima di inviarla.

## Per qualcosa in più

Per collegarlo agli altri strumenti dello studio, usarlo su molti lavori insieme o automatizzare
altro, scriva a liampmaher1996@gmail.com.
