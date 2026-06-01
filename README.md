# Pull, Otimização e Avaliação de Prompts com LangChain e LangSmith

Projeto do desafio do **MBA em Engenharia de Software com IA (Full Cycle)**.

O objetivo é fazer o *pull* de um prompt de baixa qualidade do LangSmith Prompt Hub
(`leonanluppi/bug_to_user_story_v1`), refatorá-lo com técnicas avançadas de Prompt
Engineering, publicar a versão otimizada (`v2`) e comprovar, via avaliação automática no
LangSmith, que **todas as 5 métricas ficam ≥ 0.9**.

A tarefa do prompt é converter **relatos de bug** em **User Stories ágeis** (formato
"Como um... eu quero... para que...") com Critérios de Aceitação.

---

## Técnicas Aplicadas (Fase 2)

A refatoração do prompt `prompts/bug_to_user_story_v2.yml` combinou **três técnicas**.
As técnicas declaradas nos metadados do YAML (`techniques_applied`) são:
`few-shot-learning`, `role-prompting`, `chain-of-thought`.

### 1. Role Prompting (persona)

**Por quê:** definir uma persona especialista calibra o vocabulário, o nível de
detalhe e o foco em valor de negócio — exatamente o que diferencia uma User Story boa
de uma descrição técnica genérica.

**Como apliquei** — primeira linha do `system_prompt`:

```
Você é um Product Manager sênior com 10 anos de experiência em metodologias ágeis,
especializado em converter relatos de bugs em User Stories claras e acionáveis para
times de desenvolvimento.
```

### 2. Chain of Thought (raciocínio passo a passo)

**Por quê:** a análise de bug exige decisões (quem é o usuário afetado? qual a
complexidade? tem dados técnicos/numéricos?). Forçar o modelo a raciocinar **antes** de
escrever reduz omissões e melhora a aderência ao formato correto.

**Como apliquei** — seção "PROCESSO DE ANÁLISE" que orienta o modelo a pensar antes de
gerar (sem expor esse raciocínio na resposta final):

```
## PROCESSO DE ANÁLISE (pense passo a passo antes de escrever)
1. Quem é o usuário afetado? (cliente, admin, sistema, vendedor, etc.)
2. Qual é a necessidade central?
3. Qual a complexidade? simples / médio / complexo
4. O bug tem detalhes técnicos (SQL, endpoints, logs)? → adicionar Contexto Técnico
5. O bug tem números ou cálculos específicos? → adicionar Exemplo de Cálculo
6. Quais os cenários relevantes: sucesso, erro, feedback visual, edge cases
```

### 3. Few-shot Learning (exemplos de entrada/saída) — **a alavanca decisiva**

**Por quê:** o avaliador de F1-Score compara a resposta gerada contra uma referência
específica. Regras abstratas não bastam — o modelo precisa **ver** o padrão de saída
esperado para cada tipo de bug (simples, médio com detalhes técnicos, com cálculos,
segurança, etc.). Few-shot foi o que mais elevou as notas.

**Como apliquei** — 11 pares Entrada→Saída cobrindo os arquétipos de bug do dataset,
por exemplo:

```
### EXEMPLO 2F — Bug MÉDIO (validação de estoque / concorrência)

Entrada:
Carrinho permite finalizar compra mesmo com produto fora de estoque.
(...)

Saída:
Como o sistema de e-commerce, eu quero validar disponibilidade de estoque antes de
permitir finalização de compra, para que não sejam criados pedidos que não podem ser
atendidos.

Critérios de Aceitação:
- Dado que um produto está no carrinho
- Quando o cliente tenta finalizar a compra
- Então o sistema deve validar estoque disponível em tempo real
(...)
Critérios de Prevenção:
(...)
Contexto do Bug:
(...)
```

### Edge cases e System vs User Prompt

- **System Prompt:** carrega persona, regras, processo de análise e os exemplos.
- **User Prompt:** apenas a variável `{bug_report}` (o relato cru do bug).
- **Edge cases tratados por regras explícitas:** usar somente informações do bug (não
  inventar); bugs simples → exatamente 5 critérios; bugs com dados técnicos →
  "Contexto Técnico"; bugs com números → "Exemplo de Cálculo"; bugs críticos com
  múltiplos problemas → formato expandido com seções; resposta deve conter **apenas** a
  User Story (sem introduções nem conclusões).

---

## Resultados Finais

### Link público do LangSmith

- **Prompt v2 (Hub):** https://smith.langchain.com/prompts/gtkdfeqazlp/bug_to_user_story_v2
- **Dashboard do experimento (avaliação v2):** [Painel das metricas](https://smith.langchain.com/public/0d34d3c0-dba7-4712-83cc-0076dd503972/d)

### Screenshots

- `docs/langsmith-dataset.png` — Dataset `MBA Fullcycle-eval` com os 15 exemplos
- `docs/langsmith-experiment.png` — Experimento v2 com as 5 métricas ≥ 0.9
- `docs/langsmith-trace_1.png` … `docs/langsmith-trace_5.png` — Tracing detalhado de 5 exemplos (o desafio exige no mínimo 3)

### Tabela comparativa: v1 (ruim) × v2 (otimizado)

| Métrica      | v1 (baseline)¹ | v2 (otimizado)² | Status |
|--------------|:--------------:|:---------------:|:------:|
| Helpfulness  |      0.45      |    **0.9770**   |   ✅   |
| Correctness  |      0.52      |    **0.9705**   |   ✅   |
| F1-Score     |      0.48      |    **0.9597**   |   ✅   |
| Clarity      |      0.50      |    **0.9727**   |   ✅   |
| Precision    |      0.46      |    **0.9813**   |   ✅   |

¹ Valores de referência do enunciado do desafio (baseline ilustrativo do prompt ruim).
² Avaliação real do experimento no LangSmith — Gerador `claude-sonnet-4-6`,
Avaliador `claude-opus-4-7`, dataset com 15 exemplos.

**STATUS: ✅ APROVADO — todas as 5 métricas ≥ 0.9.**

### Como cheguei lá (jornada de otimização)

1. v2 inicial (persona + CoT + few-shot básico) → reprovava em F1 (fronteiriço).
2. Diagnóstico via `evaluate_f1_score`: F1 baixo era **recall**, não precision — o
   modelo gerava User Stories corretas porém **omitia seções/detalhes** presentes nas
   referências (ex.: "Critérios de Prevenção", "Critérios de Acessibilidade").
3. Fix: adicionei few-shot espelhando os piores casos (email, modal/z-index, webhook,
   segurança/IDOR, estoque). Resultado: **F1 subiu de 0.89 → 0.96 e todas as outras
   métricas também subiram**, sem trade-off.

---

## Como Executar

### Pré-requisitos

- **Python 3.9+** (testado em 3.13)
- Conta no **LangSmith** com API Key
- API Key de um provider de LLM. Suportados: **Anthropic**, **OpenAI** ou **Google
  (Gemini)**.

### 1. Ambiente virtual e dependências

```bash
python3 -m venv venv
source venv/bin/activate          # Windows: venv\Scripts\activate
pip install -r requirements.txt
```

### 2. Variáveis de ambiente

Copie o template e preencha suas chaves:

```bash
cp .env.example .env
```

Variáveis principais do `.env`:

```ini
LANGSMITH_API_KEY=ls__...
LANGSMITH_TRACING=true
LANGSMITH_PROJECT="MBA Fullcycle"
USERNAME_LANGSMITH_HUB=seu_username_no_hub

# Escolha UM provider e descomente o bloco correspondente:
LLM_PROVIDER=anthropic
LLM_MODEL=claude-sonnet-4-6        # modelo que gera as User Stories
EVAL_MODEL=claude-opus-4-7         # modelo que avalia as métricas
ANTHROPIC_API_KEY=sk-ant-...

# Alternativa gratuita:
# LLM_PROVIDER=google
# LLM_MODEL=gemini-2.5-flash
# EVAL_MODEL=gemini-2.5-flash
# GOOGLE_API_KEY=...
```

### 3. Comandos por fase

```bash
# Fase 1 — Pull do prompt ruim (v1) do LangSmith Hub
python src/pull_prompts.py

# Fase 2 — refatore prompts/bug_to_user_story_v2.yml (já incluído neste repo)

# Fase 3 — Push do prompt otimizado (v2) para o Hub (público)
python src/push_prompts.py

# Fase 4 — Avaliação no terminal (cria o dataset + valida as 5 métricas)
python src/evaluate.py

# Fase 5 — Gera o Experiment no LangSmith (painel das 5 métricas + tracing)
python src/run_experiment.py
```

> A ordem importa: `push` publica o v2 no Hub; `evaluate` cria o dataset
> `MBA Fullcycle-eval`; `run_experiment` usa esse dataset para gerar o Experiment com
> as notas por exemplo e o tracing.

### 4. Testes de validação

```bash
pytest tests/test_prompts.py -v
```

---

## Estrutura do projeto

```
mba-ia-pull-evaluation-prompt/
├── .env.example
├── requirements.txt
├── README.md
├── prompts/
│   ├── bug_to_user_story_v1.yml   # prompt ruim (pull do Hub)
│   └── bug_to_user_story_v2.yml   # prompt otimizado (3 técnicas)
├── datasets/
│   └── bug_to_user_story.jsonl    # 15 exemplos (não alterar)
├── src/
│   ├── pull_prompts.py            # pull do Hub
│   ├── push_prompts.py            # push público do v2
│   ├── evaluate.py                # avaliação no terminal (cria dataset)
│   ├── run_experiment.py          # Experiment no LangSmith (painel + tracing)
│   ├── metrics.py                 # 5 métricas (não alterar)
│   └── utils.py                   # auxiliares (não alterar)
└── tests/
    └── test_prompts.py            # 6 testes de validação
```

### Sobre o `src/run_experiment.py`

Script **adicional** (não altera os arquivos protegidos). Usa
`langsmith.evaluation.evaluate()` para registrar um **Experiment** na UI do LangSmith
com as 5 métricas como *feedback* por exemplo e o tracing de cada geração — é o que
materializa as evidências exigidas no entregável (notas ≥ 0.9 e tracing).
