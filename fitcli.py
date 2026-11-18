"""
fitcli.py - Interface de linha de comandos     [Lisandro Freitas - A115386]

Liga tudo com o typer + alínea e) workout + exportação para CSV + extras.

Uso:  python fitcli.py --help
"""
import csv
import json
from typing import Optional

import typer

import analise
import api

app = typer.Typer(help="CLI de exercício físico com a API wger (ALPCD - TP1)")


def mostrar(dados):
    """Escreve no terminal em JSON bonito (com acentos)."""
    typer.echo(json.dumps(dados, indent=2, ensure_ascii=False))


def erro(mensagem):
    typer.secho(f"Erro: {mensagem}", fg=typer.colors.RED, err=True)
    raise typer.Exit(1)


# ------------------------------------------------------------ a) até d)
@app.command()
def top(n: int = typer.Argument(..., min=1, help="Número de exercícios")):
    """a) Lista os N exercícios mais recentes."""
    mostrar(api.top(n))


@app.command()
def search(termo: str = typer.Argument(..., help="Músculo ou categoria (ex: biceps)"),
           n: int = typer.Argument(..., min=1, help="Número de resultados")):
    """b) Pesquisa exercícios por músculo e/ou categoria."""
    try:
        mostrar(api.search(termo, n))
    except ValueError as e:
        erro(e)


@app.command("type")
def tipo(exercise_id: int = typer.Argument(..., help="Id do exercício")):
    """c) Tipo de esforço de um exercício (compound/isolated/cardio/other)."""
    try:
        typer.echo(analise.tipo(exercise_id))
    except RuntimeError:
        erro(f"exercício {exercise_id} não encontrado")


@app.command()
def equipment(categoria: str = typer.Argument(..., help="Categoria (ex: chest)")):
    """d) Conta o equipamento mencionado nas descrições de uma categoria."""
    try:
        mostrar(analise.equipment(categoria))
    except ValueError as e:
        erro(e)


# ------------------------------------------------------------------ e)
ESFORCOS = ["compound", "isolated", "any"]


def plano_treino(alvos, esforco, n):
    """
    Para cada músculo/categoria: vai buscando exercícios (b), calcula o
    tipo (c) e guarda os que têm o tipo pedido, até ter N.
    """
    plano = {}
    for alvo in alvos:
        escolhidos = []
        for ex in api.procurar(alvo):
            t = analise.tipo_esforco(ex)
            if esforco == "any" or t == esforco:
                escolhidos.append({**api.resumo(ex), "type": t})
            if len(escolhidos) == n:
                break
        plano[alvo] = escolhidos
    return plano


def exportar_csv(plano, ficheiro):
    """Escreve o plano num CSV (uma linha por exercício). Devolve nº de linhas."""
    linhas = 0
    with open(ficheiro, "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["target", "name", "type", "category", "muscles", "equipment"])
        for alvo, lista in plano.items():
            for ex in lista:
                w.writerow([alvo, ex["name"], ex["type"], ex["category"],
                            "; ".join(ex["muscles"]), "; ".join(ex["equipment"])])
                linhas += 1
    return linhas


@app.command()
def workout(alvos: str = typer.Argument(..., help="Músculos/categorias separados por vírgula (ex: biceps,back)"),
            esforco: str = typer.Argument(..., help="compound | isolated | any"),
            n: int = typer.Argument(..., min=1, help="Máximo de exercícios por músculo/categoria"),
            csv_file: Optional[str] = typer.Option(None, "--csv", help="Exportar o plano para este ficheiro CSV")):
    """e) Gera um plano de treino personalizado."""
    esforco = esforco.lower()
    if esforco not in ESFORCOS:
        erro(f"tipo de esforço tem de ser um de {ESFORCOS}")

    lista_alvos = [a.strip().lower() for a in alvos.split(",") if a.strip()]
    try:
        plano = plano_treino(lista_alvos, esforco, n)
    except ValueError as e:
        erro(e)

    if csv_file:
        total = exportar_csv(plano, csv_file)
        typer.echo(f"Ficheiro exportado: {csv_file} ({total} registos)")
    else:
        mostrar(plano)


# --------------------------------------------------------------- extras
@app.command()
def categorias():
    """Extra: lista as categorias e músculos que se podem pesquisar."""
    mostrar({
        "categories": [c["name"] for c in api.paginas("exercisecategory/")],
        "muscles": [m["name_en"] or m["name"] for m in api.paginas("muscle/")],
    })


@app.command()
def info(exercise_id: int = typer.Argument(..., help="Id do exercício")):
    """Extra: ficha completa de um exercício (com tipo e descrição)."""
    try:
        ex = api.exercicio(exercise_id)
    except RuntimeError:
        erro(f"exercício {exercise_id} não encontrado")
    mostrar({**api.resumo(ex),
             "type": analise.tipo_esforco(ex),
             "description": " ".join(api.descricao(ex).split())})


if __name__ == "__main__":
    app()
