# services/llm_guard

Writes the review note with the LLM behind guardrails G1-G8, with a template fallback when the LLM is off, fails or is blocked. `POST /review`. Built in #40-#45.

**LLM (decided in #3):** Azure OpenAI `gpt-4.1-mini` (1.35 s per note, about $0.38 per 1,000 notes). The tested alternative is a local Ollama model (`granite4:3b`, 4.3 s on the laptop GPU, 14.3 s on CPU).

`llm_spike.py` is the #3 comparison: one realistic test case (a Dutch listing, a hazard prediction, 3 real alerts), timed over 5 runs and checked against G4 (schema), G5 (citations) and G6 (wording). Its prompt and JSON schema are the first draft for #43. Commands run from `searchashouses/`:
- `python services/llm_guard/llm_spike.py ollama granite4:3b [--cpu]`
- `python services/llm_guard/llm_spike.py azure gpt-4.1-mini` (needs `AZURE_OPENAI_ENDPOINT` and `AZURE_OPENAI_API_KEY`)
