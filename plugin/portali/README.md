# Portali

Prepara una pratica del Comune di Napoli su impresainungiorno (SUE e SUAP) partendo dai documenti
del suo cliente, e si ferma dove comincia la sua parte: le dichiarazioni, la firma digitale, il
pagamento e l'invio. Gratuito e open source.

## Installazione

Nell'app Claude per computer, un solo comando aggiunge e installa Portali:

```
/plugin install portali --marketplace liammaher/portali
```

Poi scriva «Configura Portali»: Claude prepara il suo archivio privato, cifrato, su questo
computer. Lì restano i dati suoi, dello studio e dei clienti; Claude non li vede mai.

## Come si usa

1. Metta i documenti di ogni lavoro in una cartella: visura, atto o contratto, documento
   d'identità, relazione tecnica, elaborati.
2. Scriva una riga: «CILA per il signor Bianchi, i documenti sono nella cartella Bianchi».
3. Risponda all'unico messaggio di domande, confermi con Touch ID (o Windows Hello), acceda con
   SPID nel browser dell'app e scriva sul portale il codice che compare sullo schermo.
4. Quando la bozza è pronta, legga la pagina di riepilogo: cosa resta da fare a lei, ogni
   controllo fatto, ogni valore inserito.

## Dove vanno i dati dei suoi clienti

Nel suo archivio su questo computer e sul portale. Da nessun'altra parte: Portali non ha un
server. Lei è titolare del trattamento dei dati dei suoi clienti: in Claude disattivi «Aiuta a
migliorare Claude» (Impostazioni → Privacy) e usi il browser dell'app, non Claude in Chrome.

## Cosa contiene

- La compilazione automatica dell'intera pratica sul portale, con la rilettura di ogni valore.
- La biblioteca pratiche-napoli: cosa chiede ogni ufficio di Napoli per ogni procedimento, con
  le fonti.
- I casi che una pratica non copre ancora: vengono rifiutati prima di aprire il portale.

Claude non spunta mai una dichiarazione, non firma, non paga e non invia.

## Prima di usarlo

Legga l'[uso responsabile](https://github.com/liammaher/portali/blob/main/docs/responsible-use.md):
lei firma e risponde della pratica, una pratica alla volta con il suo SPID, nessun dato personale
in una segnalazione. Per chiedere una pratica o segnalare un portale cambiato apra una
[segnalazione](https://github.com/liammaher/portali/issues/new/choose).

## Per qualcosa in più

Per collegarlo agli altri strumenti dello studio, usarlo su molti lavori insieme o automatizzare
altro, scriva a liampmaher1996@gmail.com.
