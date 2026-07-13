# AIEF — AI Ethics Impact Framework (web app)

Free-text AI research proposal in → structured ethics assessment out, grounded in a KG of 217 requirements (REAMS / EU AI Act / Horizon Europe / ACM-NeurIPS), 70 AIAAIC incidents, and EU Charter rights mappings.

## Deploy to Vercel (5 minutes)

1. **Replace the KG snapshot.** Copy `scripts/export_kg_snapshot.py` into `~/Dissertation/ethics-rag/`, adjust the SPARQL property names to match your ontology, run it with GraphDB Desktop open, then copy the output over `lib/kg-snapshot.json`. (The bundled file is sample data so the app runs immediately.)
2. **Push to GitHub:**
   ```bash
   cd aief-app
   git init && git add -A && git commit -m "AIEF web app"
   gh repo create aief-app --private --source=. --push   # or push to your existing repo
   ```
3. **Import into Vercel:** vercel.com → Add New → Project → import the repo. Framework auto-detects as Next.js.
4. **Set environment variables** in Vercel → Project → Settings → Environment Variables:
   - `GROQ_API_KEY` — your key from console.groq.com
   - `MODEL_NAME` — `llama-3.3-70b-versatile`
   - `USE_LIVE_KG` — `false`
5. Deploy. Done.

## Local dev
```bash
npm install
# put your GROQ_API_KEY in .env.local
npm run dev   # http://localhost:3000
```
Test the API directly:
```bash
curl -X POST http://localhost:3000/api/assess \
  -H 'Content-Type: application/json' \
  -d '{"proposalText":"We propose a facial recognition system to monitor student attendance in schools, processing biometric data of children.","model":"llama-3.3-70b-versatile"}'
```

## Future changes
| Change | File |
|---|---|
| Switch LLM provider | `lib/llm.ts` only (Ollama/Anthropic snippets included in comments) |
| Live GraphDB | set `USE_LIVE_KG=true` + `GRAPHDB_ENDPOINT`, port SPARQL into `retrieveFromGraphDB()` in `lib/kg-retrieval.ts` |
| New model option | add to `MODELS` in `components/ProposalInput.tsx` |
| Change prompt | `lib/prompt-builder.ts` (keep in sync with Python `prompt_builder.py`) |
| Keyword extraction | `KEYWORDS_MAP` in `lib/kg-retrieval.ts` — mirror `extract_keywords()` |
