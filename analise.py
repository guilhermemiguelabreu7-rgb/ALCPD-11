"""
analise.py - Análise de texto com expressões regulares  [Guilherme Abreu - A113713]

  c) tipo de esforço de um exercício (compound / isolated / cardio / other)
  d) contagem de equipamento nas descrições de uma categoria
"""
import re
from collections import Counter

import api

# ------------------------------------------------------------------ c) type
# Palavras no NOME do exercício que denunciam o tipo de esforço.
OUTRO = re.compile(r"\b(stretch|stretching|mobility|breathing|massage)\b", re.I)
CARDIO = re.compile(
    r"\b(run|running|jog|sprint|jump|jumping|burpee|cardio|cycling|bike|skipping|treadmill)\b", re.I)
ISOLADO = re.compile(
    r"\b(curls?|raises?|fly|flyes?|extensions?|kickbacks?|shrugs?|crunch(es)?|pushdowns?)\b", re.I)
COMPOSTO = re.compile(
    r"\b(squats?|deadlifts?|press|rows?|pull-?ups?|chin-?ups?|dips?|lunges?|clean|snatch|thrusters?|push-?ups?)\b", re.I)


def tipo_esforco(exercicio):
    """
    Regras, por ordem:
      0. nome tipo "stretch", "breathing"...               -> other
      1. categoria "Cardio" ou nome tipo "jump", "run"...  -> cardio
      2. nome tipo "curl", "raise", "fly"...               -> isolated
      3. nome tipo "squat", "press", "row"...              -> compound
      4. senão conta os músculos envolvidos:
         3 ou mais -> compound | 1 ou 2 -> isolated | 0 -> other
    """
    nome = api.nome(exercicio) or ""
    if OUTRO.search(nome):
        return "other"
    if exercicio["category"]["name"] == "Cardio" or CARDIO.search(nome):
        return "cardio"
    if ISOLADO.search(nome):
        return "isolated"
    if COMPOSTO.search(nome):
        return "compound"

    n_musculos = len(exercicio["muscles"]) + len(exercicio["muscles_secondary"])
    if n_musculos >= 3:
        return "compound"
    if n_musculos >= 1:
        return "isolated"
    return "other"


def tipo(exercise_id):
    """c) Tipo de esforço a partir do id."""
    return tipo_esforco(api.exercicio(exercise_id))


# ------------------------------------------------------------- d) equipment
# Apanha "barbell", "dumbbells", "body weight", "cable machine"... (o "s?"
# fica FORA do grupo para o plural contar como o singular).
EQUIPAMENTO = re.compile(
    r"\b(barbell|dumbbell|kettlebell|cable|machine|body\s?weight|bench|band|ball|mat|ring|trx)s?\b",
    re.I,
)


def equipamento_no_texto(texto):
    """Lista de equipamentos mencionados num texto (normalizados)."""
    return [re.sub(r"\s", "", m).lower() for m in EQUIPAMENTO.findall(texto)]


def equipment(categoria):
    """d) Conta menções a equipamento nas descrições de uma categoria."""
    cid = api.categoria_id(categoria)
    if cid is None:
        raise ValueError(f"Categoria '{categoria}' não existe")

    contagem = Counter()
    for ex in api.exercicios({"category": cid}):
        contagem.update(equipamento_no_texto(api.descricao(ex)))

    # most_common() já vem ordenado por ordem decrescente
    return [{equip: total} for equip, total in contagem.most_common()]
