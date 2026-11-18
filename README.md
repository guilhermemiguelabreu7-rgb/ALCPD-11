# fitcli – TP1 ALPCD 2026/27

CLI em Python para pesquisar exercícios físicos na API pública [wger](https://wger.de/api/v2/).

## Grupo

| Aluno | Nº | Responsável por |
|---|---|---|
| Samuel Brito | A113778 | `api.py` – pedidos, User-Agent, status code, paginação, a) `top`, b) `search` |
| Guilherme Abreu | A113713 | `analise.py` – expressões regulares, c) `type`, d) `equipment` |
| Lisandro Freitas | A115386 | `fitcli.py` – CLI com typer, e) `workout`, exportação CSV, extras |

## Instalar e correr

```bash
pip install -r requirements.txt
python fitcli.py --help
```

## Comandos

```bash
python fitcli.py top 10                         # a) 10 exercícios mais recentes
python fitcli.py search biceps 5                # b) 5 exercícios de bíceps
python fitcli.py type 91                        # c) -> isolated
python fitcli.py equipment chest                # d) equipamento mais falado em "Chest"
python fitcli.py workout biceps,back compound 5 # e) plano de treino
python fitcli.py workout chest,shoulders isolated 3 --csv treino.csv
python fitcli.py categorias                     # extra: o que se pode pesquisar
python fitcli.py info 2762                      # extra: ficha completa de um exercício
```

## Como funciona

```
fitcli.py  (comandos)  ──►  analise.py  (regex: tipo, equipamento)
     │                           │
     └──────────────►  api.py  (pedidos HTTP + paginação)  ──►  wger.de
```

- **Paginação:** `api.paginas()` segue o campo `next` da resposta até ser `None`.
  É um gerador, por isso só pede mais páginas quando são precisas.
- **Inglês:** a API devolve várias traduções, por isso escolhemos a que tem `language == 2`.
- **Tipo de esforço (c):** primeiro procuram-se palavras no nome (`curl`, `raise` → isolated;
  `squat`, `press`, `row` → compound; `run`, `jump` ou categoria Cardio → cardio;
  `stretch` → other). Se nenhuma bater certo, contam-se os músculos:
  3 ou mais → compound, 1 ou 2 → isolated.
- **Equipamento (d):** uma regex procura `barbell`, `dumbbell`, `cable`, `machine`,
  `bodyweight`, etc. nas descrições, conta os plurais como o singular e ordena com `Counter.most_common()`.
- **Workout (e):** reutiliza `api.procurar()` (b) e `analise.tipo_esforco()` (c).
