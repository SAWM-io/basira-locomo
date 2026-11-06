"""Recompte les résultats LoCoMo de SAWM & Basira Memory liquide à partir des réponses jugées publiées.

Aucune dépendance, aucun appel réseau, aucune clé : le script lit les verdicts écrits par les juges,
question par question, et redonne tous les chiffres du README.

Usage :
  python3 -I recompter.py                      # lit ../reponses/*.jsonl
  python3 -I recompter.py ../reponses/rappel-320_opus-5.5_juge-passe1.jsonl

Règles de calcul (identiques à celles du protocole) :
  - score principal : questions des catégories 1 à 4 (1 540 questions), comme les autres fournisseurs ;
  - catégorie 5 (questions pièges : savoir dire que cela n'a pas été dit) : mesurée à part, avec le juge
    d'abstention ; les deux questions de la conversation 26 signalées par l'issue n° 43 du dépôt LoCoMo
    (champ "retiree") sont écartées, soit 444 questions sur 446 ;
  - contexte : médiane, sur les questions des catégories 1 à 4, des jetons fournis au lecteur.
"""
from __future__ import annotations

import glob
import json
import math
import statistics
import sys
from pathlib import Path

CATEGORIES = {1: "multi-sauts", 2: "temporel", 3: "domaine ouvert", 4: "simple saut"}
JUGES = {"j": "juge J de Mem0", "strict": "juge strict GPT-4o (LongMemEval)"}


def lire(chemin: Path) -> list[dict]:
    return [json.loads(l) for l in chemin.read_text(encoding="utf-8").splitlines() if l.strip()]


def pct(j: int, n: int) -> str:
    return f"{100 * j / n:.2f} %"


def wilson(j: int, n: int, z: float = 1.96) -> tuple[float, float]:
    p = j / n
    d = 1 + z * z / n
    c = (p + z * z / (2 * n)) / d
    m = z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / d
    return 100 * (c - m), 100 * (c + m)


def mcnemar_exact(seul_1: int, seul_2: int) -> float:
    """Test exact de McNemar (binomial bilatéral) sur les paires discordantes."""
    n, k = seul_1 + seul_2, min(seul_1, seul_2)
    if n == 0:
        return 1.0
    return min(1.0, 2 * sum(math.comb(n, i) for i in range(k + 1)) / 2 ** n)


def p_txt(p: float) -> str:
    return "< 0.001" if p < 0.001 else f"= {p:.2f}"


def verifier(entrees: list[dict], f: str) -> None:
    ids = [e["question_id"] for e in entrees]
    if len(ids) != len(set(ids)):
        raise SystemExit(f"{f} : question_id en double.")


def compter(entrees: list[dict], juge: str, cats=(1, 2, 3, 4)):
    lignes = [e for e in entrees if e["categorie"] in cats and juge in e["juges"] and not e.get("retiree")]
    return sum(1 for e in lignes if e["juges"][juge]["verdict"]), len(lignes)


def rapport(f: Path) -> dict[str, dict[str, bool]]:
    entrees = lire(f)
    verifier(entrees, f.name)
    print(f"\n{f.name}")
    modeles = sorted({v["modele"] for e in entrees for v in e["juges"].values()})
    print(f"  juges : {', '.join(modeles)}")
    for juge, nom in JUGES.items():
        j, n = compter(entrees, juge)
        lo, hi = wilson(j, n)
        print(f"  {nom} : {j}/{n} = {pct(j, n)}  (Wilson 95 % : {lo:.2f} - {hi:.2f})")
        par = []
        for c, lib in CATEGORIES.items():
            jc, nc = compter(entrees, juge, (c,))
            par.append(f"{lib} {pct(jc, nc)} ({nc})")
        print("    par catégorie : " + " ; ".join(par))
    j5, n5 = compter(entrees, "abstention", (5,))
    if n5:
        print(f"  Catégorie 5 (questions pièges), juge d'abstention : {j5}/{n5} = {pct(j5, n5)}")
    ctx = [e["contexte_jetons"] for e in entrees if e["categorie"] in CATEGORIES]
    part = [e["part_conversation"] for e in entrees if e["categorie"] in CATEGORIES]
    print(f"  contexte médian : {statistics.median(ctx):,.0f} jetons".replace(",", " ")
          + f" ({100 * statistics.median(part):.0f} % de la conversation)")
    # Questions dont TOUS les tours de preuve officiels (champ evidence du jeu) sont parmi les souvenirs rendus.
    cov = [e["preuves_toutes_rendues"] for e in entrees
           if e["categorie"] in CATEGORIES and e.get("preuves_toutes_rendues") is not None]
    if cov:
        print(f"  toutes les preuves rendues par la mémoire : {sum(cov)}/{len(cov)} = {pct(sum(cov), len(cov))}")
    return {j: {e["question_id"]: e["juges"][j]["verdict"] for e in entrees
                if e["categorie"] in CATEGORIES and j in e["juges"]} for j in JUGES}


def comparaison(b: dict, c: dict, passe: int) -> None:
    for juge, nom in JUGES.items():
        ids = sorted(set(b[juge]) & set(c[juge]))
        jb = sum(b[juge][i] for i in ids)
        jc = sum(c[juge][i] for i in ids)
        s1 = sum(1 for i in ids if b[juge][i] and not c[juge][i])
        s2 = sum(1 for i in ids if c[juge][i] and not b[juge][i])
        ecart = 100 * (jb - jc) / len(ids)
        print(f"  passe {passe}, {nom}, {len(ids)} questions communes : mémoire {jb} ({pct(jb, len(ids))}), "
              f"conversation complète {jc} ({pct(jc, len(ids))}), écart {ecart:+.1f} point, "
              f"p {p_txt(mcnemar_exact(s1, s2))} (McNemar exact, {s1} / {s2} discordantes)")


def main() -> None:
    args = sys.argv[1:]
    fichiers = sorted(args or glob.glob(str(Path(__file__).resolve().parent.parent / "reponses" / "*.jsonl")))
    if not fichiers:
        raise SystemExit("Aucun fichier de réponses.")
    verdicts = {}
    for f in fichiers:
        verdicts[Path(f).name] = rapport(Path(f))
    for nom_b, titre in (("rappel-320", "rappel jusqu'à 320 souvenirs"), ("rappel-160", "rappel jusqu'à 160 souvenirs")):
        for passe in (1, 2):
            b = verdicts.get(f"{nom_b}_opus-5.5_juge-passe{passe}.jsonl")
            c = verdicts.get(f"conversation-complete-310_opus-5.5_juge-passe{passe}.jsonl")
            if b and c:
                if passe == 1:
                    print(f"\nComparaison avec la conversation complète (mêmes questions, {titre}) :")
                comparaison(b, c, passe)


if __name__ == "__main__":
    main()
