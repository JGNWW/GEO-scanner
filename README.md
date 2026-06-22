# GEO-scanner

Generative Engine Optimization scanner voor NederlandWereldwijd. Meet hoe vindbaar pagina's en het merk zijn in grote taalmodellen (LLM's).

De MVP gebruikt alleen **Google Gemini** met web-grounding (gratis tier, geen creditcard nodig). De architectuur ondersteunt later extra providers (OpenAI, Anthropic, Perplexity).

## Wat de scanner doet

Voor elke prompt in `prompts.yaml`:

1. Stuurt de prompt naar Gemini met `google_search` grounding.
2. Verzamelt het antwoord, geciteerde URL's en genoemde organisaties.
3. Scoort of NederlandWereldwijd genoemd wordt, of pagina's geciteerd zijn, en hoe de positie is t.o.v. concurrenten (rijksoverheid.nl, IND, etc.).
4. Schrijft resultaten naar `data/results.csv` (tijdreeks) en een leesbaar rapport in `reports/YYYY-MM-DD.md`.

## Lokaal draaien

```bash
pip install -r requirements.txt
export GEMINI_API_KEY=...        # https://aistudio.google.com/apikey
python -m scanner.main
```

## Automatisch via GitHub Actions

De workflow `.github/workflows/scan.yml` draait wekelijks (maandag 06:00 UTC) en commit de nieuwe rapporten naar de repo. Zet `GEMINI_API_KEY` als repository secret.

## Prompts beheren

Redactie past `prompts.yaml` aan via een pull request. Voeg toe, verwijder of wijzig — geen code-kennis nodig.

```yaml
- id: paspoort-buitenland
  text: "Hoe vraag ik als Nederlander in het buitenland een nieuw paspoort aan?"
  category: consulair
```

## Dashboard

Een statisch HTML-dashboard staat in `docs/`. Zet GitHub Pages aan op deze branch met source `/docs` — dan zie je een live overzicht met trend-grafiek, share-of-voice en de laatste resultaten per prompt. De scanner kopieert data en rapporten bij elke run automatisch naar `docs/`.

Lokaal bekijken:

```bash
cd docs && python -m http.server 8000
```

## Configuratie

`config.yaml` bevat het doeldomein en concurrenten waarop gescoord wordt.

## Provider toevoegen

Implementeer `scanner/llm/base.py::LLMProvider` en registreer in `scanner/llm/__init__.py`. Voeg de key toe als secret en geef hem mee aan de workflow.
