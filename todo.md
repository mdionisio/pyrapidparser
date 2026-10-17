# TODO

Riferimenti: manuali ABB in `doc/abb/official/` (non nel repository):
kernel = 3HAC050946-001, overview = 3HAC050947-001,
instructions = 3HAC050917-001.

## rapid2py / runtime

- [ ] **GOTO e label**: il codice generato contiene ancora `goto .x` / `label .x`, che
  non è Python valido (dipendeva da `run/goto.py`, solo Python 2). Va scelta una
  soluzione tra quelle proposte (vedi la sezione "GOTO" più sotto), poi va tolto
  `run/goto.py`.
- [ ] **Punti di recupero con long jump** `ERROR (56, ERR_DIVZERO)` (kernel 7.2): rapid2py
  traduce il gestore ma ignora la lista dei numeri di errore, quindi il long jump non è
  implementato.
- [ ] **CONNECT / interrupt / TRAP** (kernel 4.13, 8): rapid2py solleva
  "Connect not yet supported".
- [ ] **Gestori BACKWARD e UNDO** (kernel 6, 7.2): verificare la semantica del codice
  generato, nessun test li esegue.
- [ ] **`pi` e `dnum`**: il validatore li conosce (sono predefiniti in RAPID), ma il
  runtime `run/pyrapid.py` no: un programma che usa `pi` passa la validazione e poi
  fallisce in esecuzione.
- [ ] **DIV e MOD con operandi negativi**: rapid2py usa `//` e `%`, che in Python
  arrotondano verso -infinito. Verificare sul manuale delle istruzioni il risultato RAPID
  e correggere se diverso.
- [ ] **Late binding** `% expr % args;` (kernel 4.6): verificare il codice generato e la
  risoluzione `"modulo:procedura"`.
- [ ] **Istruzioni installate mancanti** in `default/standard.sys` (MoveJ, MoveC, ...):
  oggi rapidvalidate e rapid2py le rifiutano come procedure non definite.
- [ ] Rimuovere `run/goto.py` dopo la soluzione del GOTO.

## Parser / lexer

- [ ] **Commenti dentro RECORD** (kernel 2.10, 2.14): sono ammessi a fine riga e
  sull'ultima riga, ma il parser rifiuta qualsiasi commento dentro un RECORD.
- [ ] **Letterali ottali** `0o17` (kernel 2.5): il token `INT_CONST_OCT` è dichiarato ma
  non c'è la regola del lexer.
- [ ] **Range dei letterali numerici** (kernel 2.5, IEEE 754): non controllato.
- [ ] **Codice ereditato da pycparser** nel lexer (costanti carattere, `t_UNMATCHED_QUOTE`,
  `t_BAD_CHAR_CONST`): non esiste in RAPID, si può togliere.

## rapidvalidate

- [ ] **Routine d'ingresso senza parametri** (kernel 9.1, "Entry routines cannot have
  parameters"): si potrebbe controllare la procedura passata a `rapid2py -e`.
- [ ] **Late binding** (kernel 5.4): le procedure chiamate dallo stesso statement devono
  avere parametri compatibili. Oggi si controlla solo che il nome sia una stringa.
- [ ] **Tipi installati e semi-value** (kernel 2.16): signaldi, signaldo, ecc. non sono nel
  catalogo, quindi le espressioni che li usano non vengono controllate (serve il catalogo
  dal manuale delle istruzioni 3HAC050917).
- [ ] **TEST con valori CASE ripetuti** (kernel 4.18, "only the first is recognized"):
  potrebbe essere un warning.
- [ ] **Uso di un parametro opzionale non presente** (kernel 5.2): è un errore di
  esecuzione, staticamente si potrebbe segnalare solo l'uso fuori da `IF Present(...)`
  (warning).
- [ ] **Placeholder** (`<SMT>`, `<EXP>`, ...): sintatticamente validi, ma rapid2py non li
  può tradurre. Valutare un warning.

## GOTO: soluzioni proposte

Vincolo del manuale (kernel 4.7): "A goto statement may not transfer control into a
statement list". La label quindi è sempre nella stessa lista del GOTO o in una lista che
la contiene, e rapidvalidate lo controlla già (`goto-into-list`).

1. **Macchina a stati con eccezione (consigliata).** Ogni lista che contiene label viene
   divisa in segmenti, uno per label, ed eseguita in un ciclo di dispatch:

   ```python
   _pc = 0
   while True:
       try:
           if _pc <= 0:
               ...  # istruzioni prima della prima label
           if _pc <= 1:  # label next:
               ...
           break
       except pyrapid.Goto as goto:
           if goto.label != "next":
               raise  # label di una lista più esterna
           _pc = 1
   ```

   `GOTO next;` diventa `raise pyrapid.Goto("next")`. L'eccezione attraversa i `while`/`if`
   Python generati da WHILE/FOR/IF e arriva al dispatcher della lista che possiede la
   label. Funziona all'indietro (i cicli fatti con GOTO) e in avanti, senza ricorsione.
   `pyrapid.Goto` non deve derivare da `RapidException`, così non viene intercettata dai
   gestori ERROR. Un GOTO nella stessa lista può essere ottimizzato in `_pc = k; continue`.
2. **Funzioni annidate per ogni label (trampolino).** Il codice dopo ogni label diventa
   una funzione locale, e GOTO restituisce il nome della label al chiamante, che continua
   in un ciclo. Va bene per le label della lista principale, ma con le liste annidate
   (label dentro un WHILE) diventa complesso, e senza il ciclo di trampolino i salti
   all'indietro diventano ricorsione, con stack overflow per i cicli lunghi.
3. **Patch del bytecode** (come `run/goto.py` o il pacchetto `goto-statement`):
   dipende dalla versione di CPython (il bytecode è cambiato in 3.11, 3.12 e 3.13), è
   fragile e poco mantenuto. Sconsigliata.
4. **Supporto parziale.** Si supportano solo le label della lista principale della
   routine (un `while True` con `continue`), e rapid2py rifiuta gli altri casi con una
   diagnostica. È semplice, ma lascia fuori i salti da dentro IF/WHILE/FOR, che sono
   proprio i più comuni (`IF ... GOTO retry;`).
