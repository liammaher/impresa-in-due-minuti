# Impresa in un minuto

Prepara una pratica del SUE e SUAP del Comune di Napoli, su impresainungiorno, dai documenti del tuo
cliente (o della tua impresa). Si ferma dove comincia la tua parte: le dichiarazioni, la firma digitale, il pagamento e
l'invio: Claude non spunta mai una dichiarazione, non firma, non paga e non invia. Gratuito e
open source.

> **Per chi queste pratiche le presenta già.** Impresa in un minuto compila: non è una consulenza e non
> decide al posto tuo. Claude può sbagliare, e il controllo finale è tuo. Se non sai riconoscere un errore
> in una pratica, non usarlo.

## Provalo in pochi minuti

Dopo l'installazione scrivi **«Fammi vedere una prova»**. Claude compila sul portale vero una CILA
di prova, con committente, studio e documenti inventati, senza farti domande: tu accedi con SPID,
e in un paio di minuti vedi sul portale la bozza «PROVA NON INVIARE - CILA di prova» compilata.
Poi la cancelli da «Pratiche in bozza». Anche su un tuo caso, se non hai ancora i
documenti, basta dire «è una prova, inventa i dati».

## Cosa copre, e cosa no

- **Per ora il SUE e SUAP del Comune di Napoli**, su impresainungiorno; altri sportelli e comuni si aggiungono
  nel tempo.
  Per il SUAP: aprire, trasferire, ampliare, subentrare, sospendere o chiudere un negozio, un bar o
  ristorante, un acconciatore o un'estetista, per l'impresa che presenta con il proprio SPID. Un
  caso fuori da questi (alcolici, un edificio tutelato, un centro commerciale, un'impresa con altri
  soci) Claude lo rifiuta subito, con il motivo. Gli allegati del SUAP vanno firmati digitalmente:
  li alleghi tu, Claude non ne carica nessuno.
  Un immobile in un altro comune, un altro ente (Genio Civile, Soprintendenza, ASL, Catasto, Agenzia
  delle Entrate, Regione) o una pratica che Impresa in un minuto non conosce: Claude ti dice subito che non è
  coperta dall'automazione, e non apre nulla.
- Per ogni lavoro Claude ti dice prima se la pratica è **coperta dall'automazione** (la prepara per
  intero), se ha **solo indicazioni** (non la compila) o se **non è coperta**, e perché. Poi tu
  confermi, e solo allora si comincia.
- **Coperta** vuol dire: compilata sul portale vero con dati di prova, rileggendo ogni valore.
  Nessuna pratica reale è ancora stata inviata con Impresa in un minuto.
- Le regole vengono dalla biblioteca delle procedure, ogni fatto con la sua fonte. Ciò che la
  biblioteca non copre, Claude lo dice.

## Installazione

La guida passo passo, da mandare a un collega: **https://liammaher.github.io/impresa-in-un-minuto/**

Nell'app Claude per computer, senza terminale:

1. Apri **Personalizzazione** (Customize) e la scheda **Plugin**.
2. Clicca **Aggiungi** (Add), poi **Aggiungi marketplace** (Add marketplace) e **Aggiungi da un repository**
   (Add from a repository), scrivi `liammaher/impresa-in-un-minuto` nella casella, scegline la voce nell'elenco sotto e
   clicca **Sincronizza** (Sync).
3. Apri Impresa in un minuto, tra i **Nuovi plugin**, e clicca **Aggiungi** (Add).
4. Per aggiornarlo (Impresa in un minuto cambia quando cambia il portale): **Aggiungi** → **Gestisci marketplace**
   (Manage marketplaces) → **⋯** accanto a impresa-in-un-minuto → **Verifica aggiornamenti** (Check for updates).
   Fallo ogni tanto e prima di una pratica importante. Un avviso che propone **Concedi accesso** a
   GitHub puoi chiuderlo: non serve.

Tra parentesi i nomi dell'app in inglese. In uno studio con piano Team o Enterprise basta che lo
aggiunga l'amministratore: arriva a tutti. Se dopo **Verifica aggiornamenti** vedi ancora una versione
vecchia, rimuovi il marketplace (**Rimuovi**, stesso menu), chiudi e riapri l'app e aggiungilo di nuovo
(punto 2).

Poi apri nell'app la cartella dei tuoi lavori, con una sottocartella per ogni lavoro. I dati dello
studio li chiede Claude alla prima pratica, una volta sola.
Serve Python 3 sul computer: su un Mac che non lo ha, alla prima pratica macOS propone di
installare gli strumenti per sviluppatori di Apple, che lo contengono; accetta. Su Windows
installalo da python.org.

## Come si usa

1. Metti i documenti di ogni lavoro in una cartella, una per lavoro: visura, atto o contratto,
   documento d'identità, relazione tecnica, elaborati. Meglio non allegarli alla conversazione:
   se lo fai, Claude li copia nella cartella, o ti chiede di salvarli lì.
2. Scrivi una riga: «CILA per il signor Bianchi, i documenti sono nella cartella Bianchi».
3. Claude risponde con un solo messaggio: se la pratica è coperta, cosa dicono i documenti,
   quale pratica propone, le poche domande. Rispondi una volta.
4. Accedi con SPID nel browser dell'app e scrivi a Claude «fatto». Claude compila la bozza: non
   toccare la pagina finché non ti scrive. Poi confronta l'anteprima del portale con i documenti.
5. Quando la bozza è pronta, Claude ti scrive in poche righe cosa controllare e cosa resta a te
   sul portale: l'anteprima, le dichiarazioni, la firma, il pagamento e l'invio.
6. Dopo l'invio, Claude ti dice le prossime scadenze e la pratica che di solito segue.

## Dove vanno i dati dei tuoi clienti

Nella cartella dei tuoi lavori su questo computer, nella conversazione con Claude e sul portale.
Impresa in un minuto non ha un server suo.
**Claude legge i documenti del lavoro**, compila la bozza e la confronta con essi: i dati dei
clienti (nomi, codici fiscali, indirizzi, dati catastali) passano quindi dalla conversazione con
Claude, come ogni documento che tu vi apri. Claude te lo dice alla prima pratica. Se un cliente
non vuole che i suoi documenti passino da Claude, non usare Impresa in un minuto per quel lavoro.
Password, PIN e accesso SPID mai: l'accesso al portale lo fai tu.
Sei titolare del trattamento dei dati dei tuoi clienti. In Claude disattiva «Aiuta a
migliorare Claude» (Impostazioni → Privacy) e usa il browser dell'app, non Claude in Chrome.

## Prima di usarlo

Impresa in un minuto **non è uno strumento ufficiale**: non è affiliato al Comune di Napoli, a
InfoCamere (che gestisce impresainungiorno) né ad altri enti, e non è una consulenza legale. Il nome
gioca con quello del portale, ma è un progetto indipendente, gratuito e open source.

Leggi l'[uso responsabile](https://github.com/liammaher/impresa-in-un-minuto/blob/main/docs/responsible-use.md).
In breve: tu firmi e rispondi della pratica; una pratica alla volta, con il tuo SPID; nessun dato
personale in una segnalazione. Per chiedere una pratica o segnalare un portale cambiato apri una
[segnalazione](https://github.com/liammaher/impresa-in-un-minuto/issues/new/choose).
Se qualcosa di Impresa in un minuto non funziona, dillo a Claude: ti prepara la segnalazione già
compilata, senza i dati dei clienti, e tu la rileggi prima di inviarla.

## Per qualcosa in più

Per collegarlo agli altri strumenti dello studio, usarlo su molti lavori insieme o automatizzare
altro, scrivi a liampmaher1996@gmail.com.
