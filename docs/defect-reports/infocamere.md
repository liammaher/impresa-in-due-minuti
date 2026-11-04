# Segnalazione al gestore di impresainungiorno (InfoCamere): moduli SUE del Comune di Napoli

Cinque punti in cui i moduli del Sportello Unico per l'Edilizia del Comune di Napoli
(codice catastale F839) su impresainungiorno non permettono di dichiarare ciò che la legge e il
modulo nazionale chiedono. Nei punti 1-3 il modulo nazionale (repository
`InfoCamereSCpA/Sistema-Informatico-degli-Sportelli-Unici-Moduli-PA`, commit `fc13e08` del 12
marzo 2026) ha la struttura giusta e il portale la rende in modo diverso; nel punto 4 è il modulo
nazionale stesso a non avere la riga; nel punto 5 il confronto con il modulo nazionale non è stato
fatto. Se un punto dipende dalla configurazione del Comune, vi preghiamo di inoltrarlo a chi la
cura.

Ogni punto è stato verificato su una bozza con dati inventati ("PROVA NON INVIARE"), senza salvare
né inviare nulla. Non contiene dati personali.

## 1. SCIA in sanatoria, art. 36-bis c. 1 (Salva Casa): datazione, oblazione e proposta di opere sono un solo campo

- **Dove**: SCIA edilizia con la scelta "Le opere ricadono nell'ambito della Sanatoria", sezione
  "Asseverazione SCIA - Stato legittimo, Dichiarazione di tolleranze, Sanatoria e regolarizzazioni
  per interventi già realizzati e in corso di esecuzione", caso "un intervento soggetto a SCIA
  realizzato in assenza della SCIA stessa o in difformità da essa, che risulta conforme alla
  disciplina urbanistica vigente al momento della presentazione [...] e ai requisiti prescritti
  dalla disciplina edilizia vigente al momento della realizzazione".
- **Cosa succede**: il caso apre quattro righe, "dà atto che la data/epoca di realizzazione
  dell'intervento", "attesta che la data/epoca di realizzazione dell'intervento", "determina
  l'oblazione dovuta" e "ai fini della sanatoria, la presente SCIA:". Sono un unico gruppo radio con
  i valori 1, 2, 3 e 4: spuntarne una toglie le altre e il modulo ne salva una sola.
- **Cosa chiedono la legge e il modulo nazionale**: la data o l'epoca delle opere (provata da
  documenti o attestata), l'oblazione determinata dal tecnico (art. 36-bis c. 5 DPR 380/2001) e se
  la SCIA propone opere per la sanatoria (c. 2). Nel modulo nazionale
  (`intervento_in_assenza_scia_fino_dieci_mila`) solo l'ultima è una scelta (`no_interventi` o
  `propone_interventi`); datazione e oblazione sono voci distinte.
- **Effetto**: una sanatoria Salva Casa di opere eseguite senza SCIA o in difformità non si può
  presentare completa sul portale.
- **Come riprodurlo**: su una bozza di SCIA in sanatoria, spuntare in sequenza le quattro righe:
  resta spuntata solo l'ultima (verificato il 1° novembre 2026). Il riquadro sismico sotto le quattro
  righe ("Quanto alla rilevanza sismica [...] art. 36-bis, comma 3-bis") funziona ed è a parte.
- **Cosa chiediamo**: tre campi distinti come nel modulo nazionale (la datazione, con le sue due
  modalità; l'oblazione; la proposta di opere).

## 2. SCIA in sanatoria, art. 34-ter: datazione e oblazione della variante sono un solo campo

- **Dove**: la stessa sezione, caso "una variante in corso d'opera, in parziale difformità dal
  titolo, rilasciato prima della data di entrata in vigore della legge 28 gennaio 1977, n. 10
  (articolo 34-ter DPR. n. 380)".
- **Cosa succede**: le tre righe "dà atto che la data/epoca di realizzazione dell'intervento" (con la
  data), "attesta che la data/epoca di realizzazione dell'intervento" (con la data) e "determina
  l'oblazione dovuta [...]" (con l'importo) hanno i valori 1, 2 e 3 di un'unica scelta: il modulo ne
  salva una.
- **Cosa chiede la legge**: art. 34-ter c. 2 e 3 DPR 380/2001: la data della variante (con i
  documenti dell'art. 9-bis c. 1-bis, o attestata dal tecnico) e il pagamento dell'oblazione
  determinata ai sensi dell'art. 36-bis c. 5. Sono dovute entrambe.
- **Effetto**: la regolarizzazione di una variante a un titolo anteriore al 1977 non si può
  presentare completa.
- **Come riprodurlo**: spuntare in sequenza le tre righe; spuntare "dà atto" toglie l'oblazione,
  spuntare "attesta" toglie "dà atto" (verificato il 2 novembre 2026). Il quadro "SANATORIA e
  regolarizzazioni" dello stesso caso (titolo variato; pagamento) funziona: sono due campi distinti.
- **Cosa chiediamo**: datazione e oblazione come scelte separate, come già il titolo e il pagamento
  nel quadro SANATORIA.

## 3. Permesso in sanatoria, art. 36-bis: lo stesso difetto sull'asseverazione del permesso

- **Dove**: Permesso di Costruire con la scelta "Le opere ricadono nell'ambito della Sanatoria ?",
  quadro sanatoria dell'asseverazione, caso "In parziale difformità [...] o con variazioni
  essenziali" (art. 36-bis).
- **Cosa succede**: i documenti allegati, la datazione (documenti o attestazione) e la proposta di
  opere sono un unico gruppo radio. Anche la presa d'atto che lo Sportello può subordinare il
  rilascio a opere strutturali sta in un gruppo radio con quella dell'oblazione.
- **Effetto**: un permesso in sanatoria ai sensi dell'art. 36-bis non si può presentare completo.
  Il caso dell'art. 36 (opere senza permesso) invece funziona.
- **Come riprodurlo**: su una bozza di permesso in sanatoria, scegliere la parziale difformità e
  spuntare le righe in sequenza (verificato il 30 ottobre 2026).
- **Cosa chiediamo**: le stesse voci separate del modulo nazionale.

## 4. Permesso in sanatoria (art. 36) in area vincolata: manca la riga per l'accertamento dell'art. 167

- **Dove**: la pratica che seleziona insieme il Permesso di Costruire (sanatoria: Sì) e
  l'"Accertamento di compatibilità paesaggistica (artt. 167-181 D.Lgs. 42/2004 - Comune)";
  asseverazione del permesso, quadro "Bene sottoposto ad autorizzazione paesaggistica".
- **Cosa succede**: "ricade in zona tutelata e le opere comportano alterazione" apre tre
  procedimenti (semplificato, ordinario, accertamento "di cui all'articolo 36-bis") e il Salva ne
  richiede uno ("il valore è obbligatorio"). Nessuno è l'accertamento dell'art. 167 che l'altro
  procedimento della stessa pratica chiede. Il modulo nazionale ha gli stessi tre
  (`procedimento_semplificato`, `procedimento_ordinario`, `procedimento_accertamento`).
- **Cosa chiede la legge**: le opere eseguite senza permesso (art. 36 DPR 380/2001) in area tutelata
  si sanano solo con la compatibilità paesaggistica accertata (art. 146 c. 4 D.Lgs. 42/2004), con
  l'accertamento dell'art. 167 c. 4-5; il parere dell'art. 36-bis c. 4 riguarda solo la parziale
  difformità e le variazioni essenziali.
- **Effetto**: una sanatoria ex art. 36 in area vincolata si può presentare solo dichiarando un
  procedimento che non è quello del caso.
- **Come riprodurlo**: con entrambi i procedimenti selezionati, spuntare l'alterazione e salvare
  senza scegliere: compare "il valore è obbligatorio" sui tre (verificato il 2 novembre 2026).
- **Cosa chiediamo**: accanto a quella dell'art. 36-bis, una riga "è assoggettato al procedimento di
  accertamento della compatibilità paesaggistica di cui agli artt. 167 e 181 del D.Lgs. 42/2004".

## 5. Permesso: va indicato un incentivo energetico anche per un progetto che non ne usa

- **Dove**: Permesso di Costruire, asseverazione, quadro "sicurezza impianti e consumi energetici".
- **Cosa succede**: il quadro si salva solo con uno degli incentivi spuntato (art. 14 c. 6 o c. 7
  D.Lgs. 102/2014, o il bonus volumetrico del 5% del D.Lgs. 28/2011); non c'è una riga per un
  progetto che non ne usa.
- **Cosa chiede la legge**: gli incentivi sono facoltà del progettista, non requisiti di ogni
  permesso.
- **Effetto**: un permesso senza incentivi energetici non si può presentare così com'è.
- **Come riprodurlo**: su una bozza di permesso, lasciare non spuntati gli incentivi e salvare il
  quadro (verificato il 29 ottobre 2026).
- **Cosa chiediamo**: una riga "nessun incentivo", o gli incentivi facoltativi.
