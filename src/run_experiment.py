"""
Cria um Experimento no LangSmith com painel visual de todas as 5 métricas.

Usa a API langsmith.evaluation.evaluate() para registrar cada exemplo
com F1-Score, Clarity, Precision, Helpfulness e Correctness visíveis
no dashboard de Experiments do LangSmith.

Uso:
    python src/run_experiment.py
"""

import os
import sys
from pathlib import Path
from dotenv import load_dotenv
from langsmith import Client
from langsmith.evaluation import evaluate
from utils import get_llm, check_env_vars, print_section_header
from metrics import evaluate_f1_score, evaluate_clarity, evaluate_precision

load_dotenv(Path(__file__).parent.parent / ".env")

_chain = None


def get_chain():
    global _chain
    if _chain is None:
        username = os.getenv("USERNAME_LANGSMITH_HUB", "")
        client = Client()
        prompt = client.pull_prompt(
            f"{username}/bug_to_user_story_v2",
            dangerously_pull_public_prompt=True,
        )
        llm = get_llm(temperature=0)
        _chain = prompt | llm
    return _chain


def target(inputs: dict) -> dict:
    response = get_chain().invoke(inputs)
    return {"output": response.content}


def all_metrics(inputs: dict, outputs: dict, reference_outputs: dict) -> list:
    """Calcula todas as 5 métricas em um único evaluator (3 chamadas LLM)."""
    question = inputs.get("bug_report", "")
    answer = outputs.get("output", "")
    reference = reference_outputs.get("reference", "")

    f1 = evaluate_f1_score(question, answer, reference)["score"]
    clarity = evaluate_clarity(question, answer, reference)["score"]
    precision = evaluate_precision(question, answer, reference)["score"]

    helpfulness = round((clarity + precision) / 2, 4)
    correctness = round((f1 + precision) / 2, 4)

    return [
        {"key": "f1_score",     "score": f1},
        {"key": "clarity",      "score": clarity},
        {"key": "precision",    "score": precision},
        {"key": "helpfulness",  "score": helpfulness},
        {"key": "correctness",  "score": correctness},
    ]


def main():
    print_section_header("EXPERIMENTO LANGSMITH — PAINEL DE MÉTRICAS")

    if not check_env_vars(["LANGSMITH_API_KEY", "USERNAME_LANGSMITH_HUB", "ANTHROPIC_API_KEY"]):
        return 1

    username = os.getenv("USERNAME_LANGSMITH_HUB", "")
    project = os.getenv("LANGSMITH_PROJECT", "prompt-optimization-challenge-resolved")
    dataset_name = f"{project}-eval"

    print(f"Dataset:    {dataset_name}")
    print(f"Prompt:     {username}/bug_to_user_story_v2")
    print(f"Gerador:    {os.getenv('LLM_MODEL', 'claude-sonnet-4-6')}")
    print(f"Avaliador:  {os.getenv('EVAL_MODEL', 'claude-opus-4-7')}")
    print()

    # Pré-carrega a chain uma única vez antes de rodar o experimento
    print("Carregando prompt e chain...")
    get_chain()
    print("Chain pronta. Iniciando experimento...\n")

    results = evaluate(
        target,
        data=dataset_name,
        evaluators=[all_metrics],
        experiment_prefix=f"{username}-bug-to-user-story-v2",
        description=(
            "Avaliação do prompt bug_to_user_story_v2 com Role Prompting, "
            "Chain of Thought e Few-shot Learning. "
            f"Gerador: {os.getenv('LLM_MODEL', 'claude-sonnet-4-6')} | "
            f"Avaliador: {os.getenv('EVAL_MODEL', 'claude-opus-4-7')}"
        ),
        metadata={
            "prompt": f"{username}/bug_to_user_story_v2",
            "generator": os.getenv("LLM_MODEL", "claude-sonnet-4-6"),
            "evaluator": os.getenv("EVAL_MODEL", "claude-opus-4-7"),
            "techniques": ["role-prompting", "chain-of-thought", "few-shot-learning"],
        },
        max_concurrency=1,
    )

    print("\n" + "=" * 50)
    print("RESULTADO DO EXPERIMENTO")
    print("=" * 50)

    scores: dict[str, list] = {}
    for r in results._results:
        for fb in r.get("evaluation_results", {}).get("results", []):
            scores.setdefault(fb.key, []).append(fb.score)

    threshold = 0.9
    all_passed = True
    for key in ["helpfulness", "correctness", "f1_score", "clarity", "precision"]:
        values = scores.get(key, [])
        if not values:
            continue
        avg = round(sum(values) / len(values), 4)
        symbol = "✓" if avg >= threshold else "✗"
        if avg < threshold:
            all_passed = False
        label = {
            "helpfulness": "Helpfulness",
            "correctness": "Correctness",
            "f1_score":    "F1-Score",
            "clarity":     "Clarity",
            "precision":   "Precision",
        }.get(key, key)
        print(f"  {label:15}: {avg:.4f} {symbol}")

    print()
    if all_passed:
        print("✅ STATUS: APROVADO - Todas as métricas >= 0.9")
    else:
        print("❌ STATUS: REPROVADO")

    print("\n🔗 Painel de Experiments:")
    print("   https://smith.langchain.com/projects")

    return 0 if all_passed else 1


if __name__ == "__main__":
    sys.exit(main())
 