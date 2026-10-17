# TODO

Riferimenti: manuali ABB in `doc/abb/official/` (non nel repository):
kernel = 3HAC050946-001, overview = 3HAC050947-001,
instructions = 3HAC050917-001.

## rapid2py / runtime

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
