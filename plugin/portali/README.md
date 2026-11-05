# Portali

Prepara una pratica del Comune di Napoli su impresainungiorno (SUE e SUAP) dai documenti del suo
cliente. Si ferma dove comincia la sua parte: le dichiarazioni, la firma digitale, il pagamento e
l'invio. Gratuito e open source.

## Installazione

Nell'app Claude per computer, un solo comando aggiunge e installa Portali:

```
/plugin install portali --marketplace liammaher/portali
```

<!-- vault -->
Poi scriva «Configura Portali»: Claude prepara il suo archivio privato, cifrato, su questo
computer. Lì restano i dati suoi, dello studio e dei clienti; Claude non li vede mai.
<!-- /vault -->
<!-- no-vault -->
Poi apra nell'app la cartella dei suoi lavori, con una sottocartella per ogni lavoro. Non c'è
altro da configurare. I dati dello studio li chiede Claude alla prima pratica, una volta sola.
<!-- /no-vault -->

## Come si usa

1. Metta i documenti di ogni lavoro in una cartella: visura, atto o contratto, documento
   d'identità, relazione tecnica, elaborati. Non li alleghi alla conversazione: passerebbero da
   Claude. Se lo fa, Claude non ne usa i dati: li copia nella cartella, o Le chiede di salvarli lì.
2. Scriva una riga: «CILA per il signor Bianchi, i documenti sono nella cartella Bianchi».
<!-- vault -->
3. Claude risponde con un solo messaggio: cosa ha letto, quale pratica serve, le poche domande.
   Risponda una volta, confermi con Touch ID (o Windows Hello).
4. Acceda con SPID nel browser dell'app e scriva sul portale il codice che compare sullo schermo.
<!-- /vault -->
<!-- no-vault -->
3. Claude risponde con un solo messaggio: cosa ha letto, quale pratica serve, le poche domande.
   Risponda una volta.
4. Acceda con SPID nel browser dell'app e scriva sul portale il codice che compare sullo schermo.
<!-- /no-vault -->
5. Quando la bozza è pronta, legga la pagina di riepilogo: cosa resta da fare a Lei, ogni
   controllo fatto, ogni valore inserito.
6. Dopo l'invio, Claude Le dice le prossime scadenze e la pratica che di solito segue.

## Dove vanno i dati dei suoi clienti

<!-- vault -->
Nel suo archivio su questo computer e sul portale. Da nessun'altra parte: Portali non ha un
server.
<!-- /vault -->
<!-- no-vault -->
Nella cartella dei suoi lavori, su questo computer, e sul portale. Da nessun'altra parte:
Portali non ha un server. I documenti li legge un programma sul suo computer. I dati arrivano al
portale sigillati sotto un codice che vede solo Lei: Claude non li vede. Passa da Claude solo ciò
che Lei scrive nella conversazione. In Cowork la finestra del codice non si apre, e passano da
Claude anche i dati: Claude glielo dice prima.
<!-- /no-vault -->
Lei è titolare del trattamento dei dati dei suoi clienti. In Claude disattivi «Aiuta a
migliorare Claude» (Impostazioni → Privacy) e usi il browser dell'app, non Claude in Chrome.

## Cosa contiene

- La compilazione automatica dell'intera pratica sul portale, con la rilettura di ogni valore.
- La biblioteca pratiche-napoli: cosa chiede ogni ufficio di Napoli per ogni procedimento, con
  le fonti.
- I casi che una pratica non copre ancora, o che il portale non accetta: Claude lo dice prima di
  aprire il portale, e Le dice cosa può fare.

Claude non spunta mai una dichiarazione, non firma, non paga e non invia.

## Prima di usarlo

Legga l'[uso responsabile](https://github.com/liammaher/portali/blob/main/docs/responsible-use.md).
In breve: Lei firma e risponde della pratica; una pratica alla volta, con il suo SPID; nessun dato
personale in una segnalazione. Per chiedere una pratica o segnalare un portale cambiato apra una
[segnalazione](https://github.com/liammaher/portali/issues/new/choose).

## Per qualcosa in più

Per collegarlo agli altri strumenti dello studio, usarlo su molti lavori insieme o automatizzare
altro, scriva a liampmaher1996@gmail.com.
