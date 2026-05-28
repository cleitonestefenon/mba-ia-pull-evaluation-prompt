"""
Script para fazer pull de prompts do LangSmith Prompt Hub.

Este script:
1. Conecta ao LangSmith usando credenciais do .env
2. Faz pull dos prompts do Hub
3. Salva localmente em prompts/bug_to_user_story_v1.yml

SIMPLIFICADO: Usa serialização nativa do LangChain para extrair prompts.
"""

import os
import sys
from pathlib import Path
from dotenv import load_dotenv
from langchain import hub
from utils import save_yaml, check_env_vars, print_section_header

load_dotenv(Path(__file__).parent.parent / ".env")

os.environ["LANGSMITH_API_KEY"] = os.getenv("LANGSMITH_API_KEY", "")
os.environ["LANGSMITH_ENDPOINT"] = os.getenv("LANGSMITH_ENDPOINT", "https://api.smith.langchain.com")


def pull_prompts_from_langsmith():
    check_env_vars(["LANGSMITH_API_KEY"])

    print_section_header("Pull de Prompts do LangSmith")

    prompt_name = "leonanluppi/bug_to_user_story_v1"
    output_path = Path(__file__).parent.parent / "prompts" / "bug_to_user_story_v1.yml"

    print(f"Fazendo pull de: {prompt_name}")
    prompt = hub.pull(prompt_name)

    role_map = {
        "SystemMessagePromptTemplate": "system",
        "HumanMessagePromptTemplate": "human",
        "AIMessagePromptTemplate": "ai",
    }

    messages = prompt.messages
    prompt_data = {
        "name": prompt_name,
        "messages": [
            {"role": role_map.get(type(msg).__name__, type(msg).__name__), "content": msg.prompt.template}
            for msg in messages
        ],
    }

    if save_yaml(prompt_data, str(output_path)):
        print(f"Prompt salvo em: {output_path}")
    else:
        print("Erro ao salvar o prompt.")
        return 1

    return 0


def main():
    """Função principal"""
    return pull_prompts_from_langsmith()


if __name__ == "__main__":
    sys.exit(main())
