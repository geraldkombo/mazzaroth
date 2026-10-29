// Plain-language + quinarian layer, ported from the reference build's
// src/lib/plain.ts, src/lib/ai-style.ts, src/lib/hourly.ts and src/lib/verses.ts.
// The engine speaks in house numbers and aspect codes; this turns every row into
// ordinary English and never prints a house number or an aspect code.
import { QUINARIES } from './_quinaries.js';

export const LIFE_AREAS = {
  1: 'Identity, Self-Image, Personal Brand',
  2: 'Finances, Values, Self-Worth',
  3: 'Communication, Siblings, Writing',
  4: 'Home, Family, Roots, Emotional Foundation',
  5: 'Creativity, Romance, Children, Pleasure',
  6: 'Health, Daily Work, Routines, Service',
  7: 'Partnerships, Marriage, Contracts',
  8: 'Sex, Intimacy, Shared Resources, Transformation',
  9: 'Philosophy, Travel, Higher Education, Publishing',
  10: 'Career, Reputation, Public Life, Legacy',
  11: 'Friends, Networks, Community, Hopes',
  12: 'Solitude, Spirituality, Retreat, Subconscious',
  13: 'Ophiuchus - Healing, Higher Service, Synthesis',
};

export const AREA_SHORT = {
  1: 'how you come across', 2: 'money and worth', 3: 'talking and writing',
  4: 'home and family', 5: 'creating and romance', 6: 'daily work and health',
  7: 'partners and contracts', 8: 'shared money and change',
  9: 'study, travel, publishing', 10: 'career and reputation',
  11: 'friends and networks', 12: 'rest and inner life', 13: 'healing and service',
};

export function areaShort(house) {
  return AREA_SHORT[house] || LIFE_AREAS[house] || 'an unlisted area';
}

const MOVING = {
  Pluto: 'strips something down to rebuild it, slowly and without asking',
  Uranus: 'breaks a routine open and forces a sudden change',
  Neptune: 'blurs the edges, so vision improves and detail gets unreliable',
  Saturn: 'tightens, tests and asks for a commitment that has to hold',
  Jupiter: 'widens the room, more offers, more scope, more spending',
  Mars: 'speeds things up and raises the temperature',
  Sun: 'puts a light on it, you are seen doing it',
  Venus: 'smooths the money and the people side for a short stretch',
  Mercury: 'puts it into words, messages, paperwork and small decisions',
  Moon: 'colours the mood for a day, nothing structural',
};

const NATAL_POINT = {
  Sun: 'your core drive and the way you want to be recognised',
  Moon: 'your private feelings and what makes you feel safe',
  Mercury: 'your thinking, speech and writing',
  Venus: 'your taste, your money habits and your close affections',
  Mars: 'your drive, your temper and how you push',
  Jupiter: 'your appetite for growth and belief',
  Saturn: 'your discipline, duty and long structures',
  Uranus: 'your need to be free of a fixed routine',
  Neptune: 'your imagination and what you idealise',
  Pluto: 'your capacity to change completely',
  'N.Node': 'the direction you are meant to be growing into',
  Chiron: 'the old wound you keep working around',
};

const ASPECT = {
  Conj: { name: 'sitting exactly on it', tone: 'neutral', effect: 'the two mix completely, so whatever happens here is direct and unmissable' },
  Sq: { name: 'at a hard right angle', tone: 'hard', effect: 'friction, something is blocked until you decide and act' },
  Opp: { name: 'directly across from it', tone: 'hard', effect: 'a tug of war, usually with another person or a competing demand' },
  Tri: { name: 'at an easy angle', tone: 'easy', effect: 'it flows with no fight, the best kind of day to start, ask or sign' },
  Sxt: { name: 'at a helpful angle', tone: 'easy', effect: 'an opening is there but nothing happens unless you take it' },
  Qnx: { name: 'at an awkward angle', tone: 'hard', effect: 'nothing lines up cleanly, you adjust rather than solve' },
  PAR: { name: 'at the same height in the sky', tone: 'neutral', effect: 'a quiet background echo, weaker than the others, it colours the week' },
};

export function aspectName(code) { return (ASPECT[code] && ASPECT[code].name) || code; }
export function aspectTone(code) { return (ASPECT[code] && ASPECT[code].tone) || 'neutral'; }

export function splitTransit(transit) {
  const parts = String(transit || '').split('->');
  return { moving: (parts[0] || transit || '').trim(), target: (parts[1] || '').trim() };
}

export function transitTitle(transit) {
  const { moving, target } = splitTransit(transit);
  return `${moving} in the sky, touching your ${target === 'N.Node' ? 'growth direction' : target}`;
}

export function explain(row) {
  const { moving, target } = splitTransit(row.transit);
  const a = ASPECT[row.aspect];
  const movingText = MOVING[moving] || 'puts pressure on it';
  const targetText = NATAL_POINT[target] || `your natal ${target}`;
  const area = areaShort(row.house);
  const what =
    `${moving} out in the sky is ${a ? a.name : row.aspect} the ${target} you were born with, the part of you that is ` +
    `${targetText}. ${moving} ${movingText}. ${a ? a.effect.charAt(0).toUpperCase() + a.effect.slice(1) : ''}. ` +
    `It shows up in one place: ${area}.`;
  const tone = (a && a.tone) || 'neutral';
  const use =
    tone === 'easy'
      ? `Green light. Put your ${area} moves on this date: launch, ask, publish, sign.`
      : tone === 'hard'
        ? `Expect resistance in ${area}. Do not start something new on this date; use it to decide, fix or renegotiate one thing.`
        : `Neutral weight. Keep the ${area} work steady and note what surfaces; it is information, not a crisis.`;
  return { title: transitTitle(row.transit), what, area, use };
}

export function explainShort(row) {
  const { moving, target } = splitTransit(row.transit);
  const a = ASPECT[row.aspect];
  const tone = a && a.tone;
  return `${moving} ${a ? a.name : row.aspect} your ${target}, landing in ${areaShort(row.house)}. ${tone === 'easy' ? 'Easy, use it.' : tone === 'hard' ? 'Friction, decide or repair.' : 'Steady, note it.'}`;
}

export const LEVEL_PLAIN = {
  PEAK: 'one of the strongest days of the decade',
  'VERY HIGH': 'a strong day, clear it in advance',
  HIGH: 'worth planning around',
  NORMAL: 'background weather',
};
export function levelPlain(level) { return LEVEL_PLAIN[level] || 'background weather'; }

// ---- text hygiene (ai-style.ts) ----
export function sanitize(t) {
  let s = String(t || '')
    .replace(/\*\*/g, '')
    .replace(/(^|\s)\*(?=\S)/g, '$1')
    .replace(/(\S)\*(?=\s|$)/g, '$1')
    .replace(/^#{1,6}\s*/gm, '')
    .replace(/[ \t]*[\u2014\u2015][ \t]*/g, ', ')
    .replace(/[\u00A0\u2007\u202F\u2009\u2060]/g, ' ')
    .replace(/[\u2010-\u2013\u2212]/g, '-')
    .replace(/[\u2018\u2019]/g, "'")
    .replace(/[\u201C\u201D]/g, '"')
    .replace(/[ \t]{2,}/g, ' ')
    .trim();
  const swaps = [
    [/\baudit\b/gi, 'check'], [/\bleverage\b/gi, 'use'], [/\boptimi[sz]e\b/gi, 'tighten'],
    [/\bsynerg\w+/gi, 'fit'], [/\bstakeholders?\b/gi, 'people'], [/\bactionable\b/gi, 'usable'],
    [/\bdeliverables?\b/gi, 'work'], [/\bbandwidth\b/gi, 'time'], [/\bholistic\b/gi, 'whole'],
    [/\brobust\b/gi, 'solid'],
  ];
  for (const [re, to] of swaps) s = s.replace(re, (m) => (m[0] === m[0].toUpperCase() ? to[0].toUpperCase() + to.slice(1) : to));
  return s;
}

// ---- zodiac / quinarian (mazzaroth.ts + hourly.ts + verses.ts) ----
const TROPICAL = ['Aries', 'Taurus', 'Gemini', 'Cancer', 'Leo', 'Virgo', 'Libra', 'Scorpio', 'Sagittarius', 'Capricorn', 'Aquarius', 'Pisces'];
export function signOf(lon) { return TROPICAL[Math.floor((((lon % 360) + 360) % 360) / 30)]; }
export function degInSign(lon) { return (((lon % 360) + 360) % 360) % 30; }
export function quinaryOf(lon) { return Math.floor(((((lon % 360) + 360) % 360)) / 5) + 1; }
export function getQuinary(index) { const i = ((Math.round(index) - 1) % 72 + 72) % 72; return QUINARIES[i]; }
export function titleCase(name) {
  return String(name).split(' ').map((w) => (w === 'or' ? w : w.charAt(0) + w.slice(1).toLowerCase())).join(' ');
}
export function primaryName(name) { return titleCase(String(name).split(/,| or /i)[0].trim()); }

export const NAIROBI_OFFSET_MIN = 180;
export function nairobiMinutes(at = new Date()) { return (at.getUTCHours() * 60 + at.getUTCMinutes() + NAIROBI_OFFSET_MIN) % 1440; }
export function activeQuinaryIndex(at = new Date()) { const since6 = (nairobiMinutes(at) - 360 + 1440) % 1440; return Math.floor(since6 / 20) + 1; }
export function clockLabel(minuteOfDay) {
  const m = ((minuteOfDay % 1440) + 1440) % 1440;
  const h = Math.floor(m / 60), mm = m % 60, h12 = h % 12 === 0 ? 12 : h % 12;
  return `${h12}:${String(mm).padStart(2, '0')} ${h < 12 ? 'a.m.' : 'p.m.'}`;
}
export function quinaryStartMinute(index) { return (360 + (((index - 1) % 72) + 72) % 72 * 20) % 1440; }
export function quinaryHourLabel(index) { const s = quinaryStartMinute(index); return `${clockLabel(s)} to ${clockLabel(s + 19)}`; }

// Gerald's natal chart (matches mazzaroth.py exactly) + verified angles.
export const NATAL = [
  { name: 'Sun', lon: 170.48, house: 1 }, { name: 'Moon', lon: 318.59, house: 7 },
  { name: 'Mercury', lon: 190.61, house: 2 }, { name: 'Venus', lon: 210.89, house: 2 },
  { name: 'Mars', lon: 175.98, house: 2 }, { name: 'Jupiter', lon: 97.78, house: 12 },
  { name: 'Saturn', lon: 277.45, house: 6 }, { name: 'Uranus', lon: 271.48, house: 6 },
  { name: 'Neptune', lon: 279.77, house: 6 }, { name: 'Pluto', lon: 223.26, house: 3 },
  { name: 'N.Node', lon: 324.42, house: 7 }, { name: 'Chiron', lon: 57.27, house: 11 },
];
export const ANGLES = { asc: 176.08, mc: 86.73 };

export function verseForTarget(target) {
  const b = NATAL.find((n) => n.name === target);
  const index = b ? quinaryOf(b.lon) : 36;
  const q = getQuinary(index);
  return { index, angel: primaryName(q.angel), ref: String(q.psalmRef).replace(/\s*\(KJV\)\s*$/, ''), text: q.psalmText, hour: quinaryHourLabel(index) };
}
