"""
api.py - Comunicação com a API wger            [Samuel Brito - A113778]

Tudo o que é "ir buscar dados" está aqui:
  - pedidos HTTP com User-Agent e verificação do status code
  - paginação (a API devolve os resultados por páginas)
  - funções de apoio para as alíneas a) top e b) search
"""
import re
import requests

BASE_URL = "https://wger.de/api/v2/"
HEADERS = {"User-Agent": "ALPCD-TP1-fitcli/1.0 (UMinho - Ciencia de Dados)"}
INGLES = 2  # id da língua inglesa na API


# ---------------------------------------------------------------- pedidos
def pedido(url, params=None):
    """Faz um GET e devolve o JSON. Dá erro se o status code não for 200."""
    resposta = requests.get(url, params=params, headers=HEADERS, timeout=20)
    if resposta.status_code != 200:
        raise RuntimeError(f"Erro {resposta.status_code} ao aceder a {resposta.url}")
    return resposta.json()


def paginas(endpoint, params=None):
    """
    Percorre TODAS as páginas de um endpoint e devolve os resultados um a um.
    A API responde com {"results": [...], "next": url_da_pagina_seguinte}.
    Como é um gerador (yield), só pede a página seguinte quando é precisa.
    """
    params = {"limit": 50, **(params or {})}
    url = BASE_URL + endpoint
    while url:
        dados = pedido(url, params)
        yield from dados["results"]
        url = dados["next"]  # None na última página
        params = None        # o link "next" já traz os parâmetros


# ---------------------------------------------------------- ler exercícios
def traducao_en(exercicio):
    """Devolve a tradução inglesa do exercício (ou None se não houver)."""
    for t in exercicio.get("translations", []):
        if t["language"] == INGLES:
            return t
    return None


def nome(exercicio):
    t = traducao_en(exercicio)
    return t["name"] if t else None


def descricao(exercicio):
    """Descrição em inglês sem as tags HTML (<p>, <li>, ...)."""
    t = traducao_en(exercicio)
    texto = t["description"] if t else ""
    return re.sub(r"<[^>]+>", " ", texto)


def resumo(exercicio):
    """Só os campos que interessam mostrar ao utilizador."""
    return {
        "id": exercicio["id"],
        "name": nome(exercicio),
        "category": exercicio["category"]["name"],
        "muscles": [m["name_en"] or m["name"] for m in exercicio["muscles"]],
        "equipment": [e["name"] for e in exercicio["equipment"]],
    }


def exercicios(params=None):
    """Exercícios (com todos os detalhes) que têm nome em inglês."""
    for ex in paginas("exerciseinfo/", {"language": INGLES, **(params or {})}):
        if nome(ex):
            yield ex


def exercicio(exercise_id):
    """Um exercício pelo seu id."""
    return pedido(f"{BASE_URL}exerciseinfo/{exercise_id}/")


# ---------------------------------------------------- categorias e músculos
def procurar_id(endpoint, termo):
    """
    Procura o id de uma categoria/músculo pelo nome.
    Primeiro tenta o nome exato ("biceps" -> Biceps), senão um nome parecido.
    """
    termo = termo.strip().lower()
    itens = list(paginas(endpoint))
    for item in itens:  # 1) nome exato
        nomes = [item.get("name", ""), item.get("name_en", "")]
        if termo in [n.lower() for n in nomes]:
            return item["id"]
    for item in itens:  # 2) nome que contém o termo
        if termo in item["name"].lower():
            return item["id"]
    return None


def categoria_id(termo):
    return procurar_id("exercisecategory/", termo)


def musculo_id(termo):
    return procurar_id("muscle/", termo)


# ------------------------------------------------------------ alíneas a) b)
def top(n):
    """a) Os N exercícios mais recentes."""
    resultado = []
    for ex in exercicios({"ordering": "-created"}):
        resultado.append(resumo(ex))
        if len(resultado) == n:
            break
    return resultado


def procurar(termo):
    """
    Gerador com os exercícios de um músculo e/ou categoria.
    Se o termo for categoria E músculo (ex: "shoulders"), junta os dois
    sem repetir exercícios.
    """
    filtros = []
    if (cid := categoria_id(termo)) is not None:
        filtros.append({"category": cid})
    if (mid := musculo_id(termo)) is not None:
        filtros.append({"muscles": mid})
    if not filtros:
        raise ValueError(f"'{termo}' não é um músculo nem uma categoria conhecida")

    vistos = set()
    for filtro in filtros:
        for ex in exercicios(filtro):
            if ex["id"] not in vistos:
                vistos.add(ex["id"])
                yield ex


def search(termo, n):
    """b) Até N exercícios de um músculo/categoria."""
    resultado = []
    for ex in procurar(termo):
        resultado.append(resumo(ex))
        if len(resultado) == n:
            break
    return resultado
