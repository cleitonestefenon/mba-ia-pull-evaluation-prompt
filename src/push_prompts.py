"""
Script para fazer push de prompts otimizados ao LangSmith Prompt Hub.

Este script:
1. Lê os prompts otimizados de prompts/bug_to_user_story_v2.yml
2. Valida os prompts
3. Faz push PÚBLICO para o LangSmith Hub
4. Adiciona metadados (tags, descrição, técnicas utilizadas)

SIMPLIFICADO: Código mais limpo e direto ao ponto.
"""

import os
import sys
from pathlib import Path
from dotenv import load_dotenv
from langchain import hub
from langchain_core.prompts import ChatPromptTemplate
from utils import load_yaml, check_env_vars, print_section_header, validate_prompt_structure

load_dotenv(Path(__file__).parent.parent / ".env")

os.environ["LANGSMITH_API_KEY"] = os.getenv("LANGSMITH_API_KEY", "")
os.environ["LANGSMITH_ENDPOINT"] = os.getenv("LANGSMITH_ENDPOINT", "https://api.smith.langchain.com")


def push_prompt_to_langsmith(prompt_name: str, prompt_data: dict) -> bool:
    """
    Faz push do prompt otimizado para o LangSmith Hub (PÚBLICO).

    Args:
        prompt_name: Nome do prompt
        prompt_data: Dados do prompt

    Returns:
        True se sucesso, False caso contrário
    """
    try:
        system_prompt = prompt_data.get("system_prompt", "")
        description = prompt_data.get("description", "")
        techniques = prompt_data.get("techniques_applied", [])

        prompt_template = ChatPromptTemplate.from_messages([
            ("system", system_prompt),
            ("human", "{bug_report}")
        ])

        print(f"Fazendo push de: {prompt_name}")

        hub.push(
            prompt_name,
            prompt_template,
            new_repo_is_public=True,
            new_repo_description=description,
            tags=techniques if techniques else None,
        )

        print(f"Prompt '{prompt_name}' publicado com sucesso no LangSmith Hub")
        print(f"Técnicas aplicadas: {', '.join(techniques)}")
        return True

    except Exception as e:
        print(f"Erro ao publicar prompt '{prompt_name}': {e}")
        return False


def validate_prompt(prompt_data: dict) -> tuple[bool, list]:
    """
    Valida estrutura básica de um prompt (versão simplificada).

    Args:
        prompt_data: Dados do prompt

    Returns:
        (is_valid, errors) - Tupla com status e lista de erros
    """
    return validate_prompt_structure(prompt_data)


def main():
    """Função principal"""
    print_section_header("Push de Prompts Otimizados ao LangSmith")

    if not check_env_vars(["LANGSMITH_API_KEY", "USERNAME_LANGSMITH_HUB"]):
        return 1

    username = os.getenv("USERNAME_LANGSMITH_HUB", "")
    prompt_file = Path(__file__).parent.parent / "prompts" / "bug_to_user_story_v2.yml"

    if not prompt_file.exists():
        print(f"Arquivo não encontrado: {prompt_file}")
        print("Crie o arquivo prompts/bug_to_user_story_v2.yml antes de continuar.")
        return 1

    print(f"Carregando prompt de: {prompt_file}")
    prompt_data = load_yaml(str(prompt_file))

    if not prompt_data:
        print("Erro ao carregar o arquivo YAML.")
        return 1

    is_valid, errors = validate_prompt(prompt_data)
    if not is_valid:
        print("Prompt inválido:")
        for error in errors:
            print(f"  - {error}")
        return 1

    print("Prompt validado com sucesso")

    prompt_name = f"{username}/bug_to_user_story_v2"
    success = push_prompt_to_langsmith(prompt_name, prompt_data)

    if not success:
        return 1

    print(f"\nConfira o prompt publicado em:")
    print(f"  https://smith.langchain.com/prompts/{username}/bug_to_user_story_v2")
    return 0


if __name__ == "__main__":
    sys.exit(main())
