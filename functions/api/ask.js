import { json, missingSecret } from '../_lib.js';
import { sanitize, areaShort, splitTransit, aspectName } from '../_plain.js';

const CEREBRAS_URL = 'https://api.cerebras.ai/v1/chat/completions';

const STYLE = `Style rules, obey strictly:
Direct, terse, operator tone. No stories, no filler, no throat-clearing, no greetings, no closing lines. No markdown headers, no asterisks, no bold syntax. Never the em-dash character; use plain hyphens, commas, colons or periods. No emojis. Prefer short compact bullets over paragraphs. Every line either states a fact from the transit rows, an action, or a warning. If nothing needs saying, say nothing.
Banned words: audit, leverage, optimize, synergy, stakeholder, actionable, deliverable, bandwidth, holistic, robust. Use the app's own vocabulary instead: quinary, window, angel, spirit, hour, cultivate, hold, peak.`;

const NATAL_CONTEXT = `Gerald: born 13 September 1989, 03:50 UTC, Nairobi. Natal Sun 170.48, the way he comes across. Ascendant 176.08, the 36th quinary, angel Menadel, hour 5:40 to 5:59 p.m. Nairobi, Psalm 26:8. Saturn and Neptune share the 56th quinary, angel Poiel, both governing his daily work and health.
Sky mapping in force: sidereal 13-sign, IAU constellation boundaries. The Sun's true backdrop is Leo, Mercury and Mars are in Virgo, Saturn and Neptune are in Sagittarius. Nothing in this chart is in Ophiuchus. Never claim otherwise.
Engine shape: only seven parts of life ever fire because only those hold his natal points: daily work and health, partners and contracts, talking and writing, how he comes across, money and worth, friends and networks, rest and inner life. Never claim anything fires in home and family, creating and romance, shared money, study and travel, career title, or healing and service. Squares dominate and easy aspects are rare, so most windows ask for a decision or a repair.
Framework: Jaime Paul Lamb, Astrological Goetia. Each 5 degree quinary carries one angel and one psalm.`;

function buildSystemPrompt(ctx) {
  const prof = ctx && ctx.profection
    ? `Age ${ctx.profection.age} year points at ${ctx.profection.name}${ctx.profection.occupants && ctx.profection.occupants.length ? ' (natal ' + ctx.profection.occupants.join(', ') + ' here)' : ''}.`
    : '';
  const hasCtx = ctx && Object.keys(ctx).length > 0;
  const emptyCtx = hasCtx ? '' : `\nNo engine reading was supplied with this question. Say plainly that today's live windows are read from the app, and answer only from the natal facts above: the fixed daily hour is Menadel, 5:40 to 5:59 p.m. Nairobi, Psalm 26:8, and give one practical action for it. Never invent transits, dates or windows.`;
  return [
    `You are Mazzaroth, Gerald Kombo's transit strategist.`,
    NATAL_CONTEXT,
    prof,
    ``,
    `Ground every line in the data provided. Never invent transits, aspects, dates or planets.`,
    `Plain language rule, absolute: never write a house number in any form, no H1, no H6, no "house 6", no "twelfth house". Name the part of life in ordinary words: how you come across, money and worth, talking and writing, daily work and health, partners and contracts, friends and networks, rest and inner life. Never write an aspect code such as Sq, Tri, Opp, Conj, Sxt, Qnx or PAR. Say hard right angle, easy angle, face-off, direct hit, small opening, awkward angle, background echo. Explain each planet in one plain clause the first time it appears.`,
    `Name the angel of the active hour at most once, with its psalm as something to read. Never name a second entity, never instruct him to call, summon, invoke, address or petition anything. The instruction is always a practical action he can take himself.`,
    `Answer the question directly and practically. 2 to 4 concrete actions, timing when the data gives it, and what to avoid. Max about 200 words.`,
    STYLE,
    ``,
    `=== ENGINE READING (ground truth, do not contradict) ===`,
    JSON.stringify(ctx).slice(0, 9000),
    emptyCtx,
  ].join('\n');
}

export async function onRequestPost(context) {
  const { request, env } = context;
  if (!env.CEREBRAS_API_KEY) return json({ error: missingSecret('CEREBRAS_API_KEY') }, 500);

  let body;
  try { body = await request.json(); } catch { return json({ error: 'Invalid JSON body.' }, 400); }

  const question = String(body.question || '').trim();
  if (question.length < 2) return json({ error: 'Ask me something.' }, 400);
  if (question.length > 3000) return json({ error: 'Question too long (max 3000 chars).' }, 400);

  const ctx = body.context && typeof body.context === 'object' ? body.context : {};
  const history = Array.isArray(body.history) ? body.history.slice(-8) : [];

  const messages = [
    { role: 'system', content: buildSystemPrompt(ctx) },
    ...history.map((m) => ({ role: m.role === 'user' ? 'user' : 'assistant', content: sanitize(String(m.content || '')).slice(0, 4000) })),
    { role: 'user', content: question },
  ];

  const model = env.AI_MODEL || 'gpt-oss-120b';

  try {
    const res = await fetch(CEREBRAS_URL, {
      method: 'POST',
      headers: { 'content-type': 'application/json', authorization: `Bearer ${env.CEREBRAS_API_KEY}` },
      body: JSON.stringify({ model, messages, max_tokens: 1200, temperature: 0.6, reasoning_effort: 'low' }),
    });
    const data = await res.json().catch(() => ({}));
    if (!res.ok) {
      const msg = data && data.error && data.error.message ? data.error.message : `Cerebras error ${res.status}`;
      return json({ error: msg }, 502);
    }
    const text = data && data.choices && data.choices[0] && data.choices[0].message ? data.choices[0].message.content : '';
    if (!text) return json({ error: 'Empty AI response.' }, 502);
    return json({ text: sanitize(text) });
  } catch (e) {
    return json({ error: 'AI request failed: ' + (e && e.message ? e.message : e) }, 502);
  }
}
