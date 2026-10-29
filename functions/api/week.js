import { json, missingSecret } from '../_lib.js';
import { sanitize, areaShort } from '../_plain.js';

const CEREBRAS_URL = 'https://api.cerebras.ai/v1/chat/completions';

const STYLE = `Style rules: direct, terse operator tone. No greetings, no stories, no markdown headers or asterisks, never the em-dash character, no emojis. Short compact bullets. Banned words: audit, leverage, optimize, synergy, stakeholder, actionable, deliverable, bandwidth, holistic, robust. Use the app's own vocabulary: quinary, window, angel, hour, cultivate, hold, peak.`;

const NATAL_CONTEXT = `Gerald: born 13 September 1989, 03:50 UTC, Nairobi. Natal Sun 170.48. Ascendant 176.08, the 36th quinary, angel Menadel, hour 5:40 to 5:59 p.m. Nairobi, Psalm 26:8. Saturn and Neptune share the 56th quinary, angel Poiel, governing his daily work and health. Only seven parts of life ever fire: daily work and health, partners and contracts, talking and writing, how he comes across, money and worth, friends and networks, rest and inner life. Never mention anything else.`;

const SYSTEM_WEEK = `You are Mazzaroth writing Gerald a 7-day operator briefing.
${NATAL_CONTEXT}

Ground everything in the transit rows. Never invent dates or transits.

Output format, strict:
"Week of <startDate>"
A bullet block "Strongest days:" listing each of the strongest days, one bullet each, format: "<YYYY-MM-DD>, <plain sentence naming the planet, what it is doing, and the part of life> - <one-line action>"
A bullet block "Build:" with 2 to 4 bullets, each tied to a specific day.
A bullet block "Hold:" with 1 to 3 bullets, each tied to a specific day.
A bullet block "Hours:" with 1 to 2 bullets on how to use the 5:40 p.m. hour this week, naming Menadel and the psalm to read. Never tell him to call or summon anything.
A bullet block "Horizon:" with 1 to 2 bullets naming the next big window beyond this week.
No prose paragraphs. No preamble. Max about 200 words. Never write a house number or an aspect code.
${STYLE}`;

export async function onRequestPost(context) {
  const { request, env } = context;
  if (!env.CEREBRAS_API_KEY) return json({ error: missingSecret('CEREBRAS_API_KEY') }, 500);

  let body;
  try { body = await request.json(); } catch { return json({ error: 'Invalid JSON body.' }, 400); }
  const startDate = String(body.startDate || '').slice(0, 10);
  if (!/^\d{4}-\d{2}-\d{2}$/.test(startDate)) return json({ error: 'A valid startDate is required.' }, 400);
  const events = Array.isArray(body.events) ? body.events.slice(0, 60) : [];
  const force = !!body.force;

  const cacheKey = `https://mz-brief.local/week/${startDate}/v2`;
  const cache = typeof caches !== 'undefined' && caches.default ? caches.default : null;
  if (cache && !force) { try { const hit = await cache.match(cacheKey); if (hit) return json({ text: await hit.text(), cached: true }); } catch {} }

  const list = events.length === 0
    ? 'No transits above threshold this week. Plan a preparation week.'
    : events.map((e) => `${e.date}: ${e.transit} ${e.aspect}, part of life: ${areaShort(e.house)}${e.meaning ? ', ' + e.meaning : ''}`).join('\n');

  const model = env.AI_MODEL || 'gpt-oss-120b';
  try {
    const res = await fetch(CEREBRAS_URL, {
      method: 'POST',
      headers: { 'content-type': 'application/json', authorization: `Bearer ${env.CEREBRAS_API_KEY}` },
      body: JSON.stringify({
        model,
        messages: [
          { role: 'system', content: SYSTEM_WEEK },
          { role: 'user', content: `Week starting ${startDate}. Transits and upcoming horizon:\n${list}\n\nWrite the outlook.` },
        ],
        max_tokens: 1400,
        temperature: 0.5,
        reasoning_effort: 'low',
      }),
    });
    const data = await res.json().catch(() => ({}));
    if (!res.ok) {
      const msg = data && data.error && data.error.message ? data.error.message : `Cerebras error ${res.status}`;
      return json({ error: msg }, 502);
    }
    const text = data && data.choices && data.choices[0] && data.choices[0].message ? data.choices[0].message.content : '';
    if (!text) return json({ error: 'Empty AI response.' }, 502);
    const clean = sanitize(text);
    if (cache) { try { await cache.put(cacheKey, new Response(clean, { headers: { 'content-type': 'text/plain; charset=utf-8', 'cache-control': 'max-age=86400' } })); } catch {} }
    return json({ text: clean, cached: false });
  } catch (e) {
    return json({ error: 'AI request failed: ' + (e && e.message ? e.message : e) }, 502);
  }
}
