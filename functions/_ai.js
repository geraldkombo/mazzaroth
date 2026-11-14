// Shared AI backend for ask/brief/week.
// Primary: Cloudflare Workers AI (free allowance, keyless via env.AI binding).
// Fallback: Cerebras chat completions, only used if CEREBRAS_API_KEY is still set.
// Returns { text, source } where source is 'workers-ai' or 'cerebras'.
// Throws Error with a user-safe message when every backend fails.

const CEREBRAS_URL = 'https://api.cerebras.ai/v1/chat/completions';

// Tried in order. llama-3.3-70b fp8-fast is the quality pick on the free tier;
// the 8b fp8 model is the congestion fallback.
const WORKERS_AI_MODELS = [
  '@cf/meta/llama-3.3-70b-instruct-fp8-fast',
  '@cf/meta/llama-3.1-8b-instruct-fp8',
];

async function runWorkersAI(env, messages, opts) {
  if (!env.AI) return null;
  let lastErr = null;
  for (const model of WORKERS_AI_MODELS) {
    try {
      const out = await env.AI.run(model, {
        messages,
        max_tokens: opts.max_tokens || 1200,
        temperature: typeof opts.temperature === 'number' ? opts.temperature : 0.6,
      });
      // Text-generation models return { response: string }. Guard against the
      // object-response gotcha seen with response_format:json_object elsewhere.
      let text = '';
      if (typeof out === 'string') text = out;
      else if (out && typeof out.response === 'string') text = out.response;
      else if (out && out.response && typeof out.response === 'object') text = JSON.stringify(out.response);
      if (text && text.trim()) return { text, source: 'workers-ai' };
      lastErr = new Error('empty response from ' + model);
    } catch (e) {
      lastErr = e;
    }
  }
  if (lastErr) throw lastErr;
  return null;
}

async function runCerebras(env, messages, opts) {
  if (!env.CEREBRAS_API_KEY) return null;
  const model = env.AI_MODEL || 'gpt-oss-120b';
  const res = await fetch(CEREBRAS_URL, {
    method: 'POST',
    headers: { 'content-type': 'application/json', authorization: `Bearer ${env.CEREBRAS_API_KEY}` },
    body: JSON.stringify({
      model,
      messages,
      max_tokens: opts.max_tokens || 1200,
      temperature: typeof opts.temperature === 'number' ? opts.temperature : 0.6,
      reasoning_effort: 'low',
    }),
  });
  const data = await res.json().catch(() => ({}));
  if (!res.ok) {
    const msg = data && data.error && data.error.message ? data.error.message : `Cerebras error ${res.status}`;
    throw new Error(msg);
  }
  const text = data && data.choices && data.choices[0] && data.choices[0].message ? data.choices[0].message.content : '';
  if (!text) throw new Error('Empty AI response.');
  return { text, source: 'cerebras' };
}

export async function runChat(env, messages, opts = {}) {
  const errors = [];

  try {
    const r = await runWorkersAI(env, messages, opts);
    if (r) return r;
    errors.push('Workers AI binding not configured');
  } catch (e) {
    errors.push('Workers AI: ' + (e && e.message ? e.message : e));
  }

  try {
    const r = await runCerebras(env, messages, opts);
    if (r) return r;
    errors.push('Cerebras key not configured');
  } catch (e) {
    errors.push('Cerebras: ' + (e && e.message ? e.message : e));
  }

  throw new Error(errors.join(' | '));
}
