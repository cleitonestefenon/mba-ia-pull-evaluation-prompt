"""
Testes automatizados para validação de prompts.
"""
import pytest
import yaml
import sys
from pathlib import Path

# Adicionar src ao path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from utils import validate_prompt_structure

PROMPT_PATH = str(Path(__file__).parent.parent / "prompts" / "bug_to_user_story_v2.yml")


def load_prompts(file_path: str):
    """Carrega prompts do arquivo YAML."""
    with open(file_path, 'r', encoding='utf-8') as f:
        return yaml.safe_load(f)


class TestPrompts:
    def test_prompt_has_system_prompt(self):
        """Verifica se o campo 'system_prompt' existe e não está vazio."""
        data = load_prompts(PROMPT_PATH)
        assert "system_prompt" in data, "Campo 'system_prompt' não encontrado no YAML"
        assert data["system_prompt"].strip() != "", "Campo 'system_prompt' está vazio"

    def test_prompt_has_role_definition(self):
        """Verifica se o prompt define uma persona (ex: 'Você é um Product Manager')."""
        data = load_prompts(PROMPT_PATH)
        system = data["system_prompt"]
        has_role = "Você é um" in system or "Product Manager" in system
        assert has_role, "O prompt não define uma persona/role (ex: 'Você é um Product Manager')"

    def test_prompt_mentions_format(self):
        """Verifica se o prompt exige formato Markdown ou User Story padrão."""
        data = load_prompts(PROMPT_PATH)
        system = data["system_prompt"]
        has_format = "Como um" in system or "User Story" in system or "Critérios de Aceitação" in system
        assert has_format, "O prompt não menciona o formato de User Story esperado"

    def test_prompt_has_few_shot_examples(self):
        """Verifica se o prompt contém exemplos de entrada/saída (técnica Few-shot)."""
        data = load_prompts(PROMPT_PATH)
        system = data["system_prompt"]
        has_examples = "EXEMPLO" in system and "Entrada:" in system and "Saída:" in system
        assert has_examples, "O prompt não contém exemplos de Few-shot (Entrada/Saída)"

    def test_prompt_no_todos(self):
        """Garante que não há nenhum [TODO] esquecido no texto."""
        data = load_prompts(PROMPT_PATH)
        system = data["system_prompt"]
        assert "[TODO]" not in system, "O prompt ainda contém marcadores [TODO] não resolvidos"

    def test_minimum_techniques(self):
        """Verifica (através dos metadados do yaml) se pelo menos 2 técnicas foram listadas."""
        data = load_prompts(PROMPT_PATH)
        techniques = data.get("techniques_applied", [])
        assert len(techniques) >= 2, (
            f"Mínimo de 2 técnicas requeridas, encontradas: {len(techniques)} ({techniques})"
        )


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
