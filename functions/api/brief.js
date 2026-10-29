import { json, missingSecret } from '../_lib.js';
import { sanitize, areaShort, explainShort, levelPlain, getQuinary, quinaryHourLabel, primaryName } from '../_plain.js';

const CEREBRAS_URL = 'https://api.cerebras.ai/v1/chat/completions';

const STYLE = `Style rules, obey strictly:
Direct, terse, operator tone. No stories, no filler, no greetings, no closing lines. No markdown headers, no asterisks, no bold. Never the em-dash character; use plain hyphens, commas, colons or periods. No emojis. Short compact bullets over paragraphs. Every line states a fact from the rows, an action, or a warning.
Banned words: audit, leverage, optimize, synergy, stakeholder, actionable, deliverable, bandwidth, holistic, robust. Use the app's own vocabulary: quinary, window, angel, spirit, hour, cultivate, hold, peak.`;

const NATAL_CONTEXT = `Gerald: born 13 September 1989, 03:50 UTC, Nairobi. Natal Sun 170.48, the way he comes across. Ascendant 176.08, the 36th quinary, angel Menadel, hour 5:40 to 5:59 p.m. Nairobi, Psalm 26:8. Saturn and Neptune share the 56th quinary, angel Poiel, both governing his daily work and health.
Sky mapping: sidereal 13-sign, IAU boundaries. The Sun's true backdrop is Leo, Mercury and Mars in Virgo, Saturn and Neptune in Sagittarius. Nothing in this chart is in Ophiuchus. Never claim otherwise.
Engine shape: only seven parts of life ever fire, because only those hold his natal points: daily work and health, partners and contracts, talking and writing, how he comes across, money and worth, friends and networks, rest and inner life. Never mention home and family, creating and romance, shared money, study and travel, career title, or healing and service: nothing of his lives there. Squares dominate and easy aspects are rare, so most windows ask for a decision or a repair.
Framework: Jaime Paul Lamb, Astrological Goetia. Each 5 degree quinary carries one angel and one psalm, and owns a 20 minute hour from 6:00 a.m. at 0 Aries.`;

const SYSTEM_BRIEF = `You are Mazzaroth, Gerald Kombo's transit strategist.
${NATAL_CONTEXT}

Ground every line in the transit rows provided. Never invent transits, aspects, dates or planets. If today is quiet, skip forward to the next active window in the upcoming list.
Name only the angel of the active hour, once, and give the psalm reference and a short fragment of it as something to read. Never name a second entity, never instruct him to call, summon, invoke, address or petition anything. The instruction is always a practical action he can take himself.

Output format, strict:
Line 1: "Today: <one-line read of today>"
Line 2: "Hour: <angel>, <hour band>, read <psalm ref>, <what that hour is for>"
Line 3: "Next window: <YYYY-MM-DD>, <plain sentence naming the planet, what it is doing, and the part of life>"
Then a bullet block "Do:" with 3 to 5 short imperative bullets tied to specific dates and named parts of life.
Then a bullet block "Hold:" with 1 to 3 short bullets for what to pace, delay, or protect.
No section beyond these. No prose paragraphs. Max about 160 words total.
${STYLE}
Plain language rule, absolute: never write a house number in any form, no H1, no H6, no "house 6", no "twelfth house". Name the part of life in ordinary words: how you come across, money and worth, talking and writing, daily work and health, partners and contracts, friends and networks, rest and inner life. Never write an aspect code such as Sq, Tri, Opp, Conj, Sxt, Qnx or PAR. Say hard right angle, easy angle, face-off, direct hit, small opening, awkward angle, background echo. Explain each planet in one plain clause the first time it appears.`;

function plainRow(e) {
  return `${e.transit} ${e.aspect}, part of life: ${areaShort(e.house)}. ${explainShort(e)}`;
}

export async function onRequestPost(context) {
  const { request, env } = context;
  if (!env.CEREBRAS_API_KEY) return json({ error: missingSecret('CEREBRAS_API_KEY') }, 500);

  let body;
  try { body = await request.json(); } catch { return json({ error: 'Invalid JSON body.' }, 400); }

  const date = String(body.date || '').slice(0, 10);
  if (!/^\d{4}-\d{2}-\d{2}$/.test(date)) return json({ error: 'A valid date is required.' }, 400);
  const events = Array.isArray(body.events) ? body.events.slice(0, 12) : [];
  const upcoming = Array.isArray(body.upcoming) ? body.upcoming.slice(0, 12) : [];
  const qIndex = Number(body.activeQuinary) >= 1 && Number(body.activeQuinary) <= 72 ? Math.round(Number(body.activeQuinary)) : null;
  const force = !!body.force;

  const cacheKey = `https://mz-brief.local/brief/${date}/q${qIndex || 0}/v2`;
  const cache = typeof caches !== 'undefined' && caches.default ? caches.default : null;
  if (cache && !force) {
    try { const hit = await cache.match(cacheKey); if (hit) return json({ text: await hit.text(), cached: true }); } catch {}
  }

  const eventsPrompt = events.length === 0
    ? 'No transits above the daily threshold today. Treat today as a preparation day for the upcoming windows below.'
    : events.map((e, i) => `${i + 1}. ${plainRow(e)} Meaning: ${e.meaning || ''}. Actions: ${(e.actions || []).join('; ')}`).join('\n');
  const upcomingPrompt = upcoming.length === 0
    ? 'No upcoming windows supplied.'
    : upcoming.map((u) => `${u.date}: ${plainRow(u)} ${u.meaning || ''}`).join('\n');

  let quinaryPrompt = 'No active quinary supplied.';
  if (qIndex) {
    const q = getQuinary(qIndex);
    quinaryPrompt = [
      `Active quinary ${q.index}, ${q.range}, hour ${quinaryHourLabel(q.index)} Nairobi.`,
      `Angel ${primaryName(q.angel)}.`,
      `Psalm ${q.psalmRef}: "${q.psalmText}"`,
      `This hour favours: ${q.angelAttributes.join(', ')}.`,
    ].join('\n');
  }

  const model = env.AI_MODEL || 'gpt-oss-120b';
  try {
    const res = await fetch(CEREBRAS_URL, {
      method: 'POST',
      headers: { 'content-type': 'application/json', authorization: `Bearer ${env.CEREBRAS_API_KEY}` },
      body: JSON.stringify({
        model,
        messages: [
          { role: 'system', content: SYSTEM_BRIEF },
          { role: 'user', content: `Date: ${date}\n\nQuinary ruling this hour:\n${quinaryPrompt}\n\nActive transits today:\n${eventsPrompt}\n\nUpcoming windows on the horizon:\n${upcomingPrompt}\n\nWrite the plan.` },
        ],
        max_tokens: 1200,
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
