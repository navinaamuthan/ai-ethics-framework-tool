// lib/llm.ts — the ONLY file that talks to an LLM provider.
// Currently Groq (OpenAI-compatible). See bottom for swap instructions.
import OpenAI from "openai"

// Instantiated lazily: the OpenAI constructor throws at import time when the
// key is missing, which breaks `next build` on Vercel during page-data collection.
let groq: OpenAI | null = null
function getClient(): OpenAI {
  if (!groq) {
    groq = new OpenAI({
      apiKey: process.env.GROQ_API_KEY ?? "",
      baseURL: "https://api.groq.com/openai/v1",
    })
  }
  return groq
}

export async function callLLM(prompt: string, model: string): Promise<string> {
  if (!process.env.GROQ_API_KEY) {
    throw new Error("GROQ_API_KEY is not set — add it in Vercel project settings.")
  }
  const response = await getClient().chat.completions.create({
    model,
    messages: [{ role: "user", content: prompt }],
    temperature: 0.3,
    max_tokens: 4000,
  })
  return response.choices[0].message.content || ""
}

/* TO SWITCH TO OLLAMA (local):
   export async function callLLM(prompt: string, model: string) {
     const res = await fetch("http://localhost:11434/api/generate", {
       method: "POST",
       body: JSON.stringify({ model, prompt, stream: false, options: { temperature: 0.3 } }),
     })
     const data = await res.json()
     return data.response
   }

   TO SWITCH TO ANTHROPIC:
   import Anthropic from "@anthropic-ai/sdk"
   const client = new Anthropic({ apiKey: process.env.ANTHROPIC_API_KEY })
   const msg = await client.messages.create({
     model: "claude-sonnet-4-6", max_tokens: 4000,
     messages: [{ role: "user", content: prompt }],
   })
   return msg.content[0].type === "text" ? msg.content[0].text : ""
*/
