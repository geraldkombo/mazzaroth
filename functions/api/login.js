import { json, timingSafeEqualStr, makeSession, cookieHeader, cookieSecure, missingSecret } from '../_lib.js';

const TTL_MS = 30 * 24 * 60 * 60 * 1000; // 30 days

export async function onRequestPost(context) {
  const { request, env } = context;
  if (!env.AUTH_EMAIL || !env.AUTH_PASS) return json({ error: missingSecret('AUTH_EMAIL') }, 500);
  if (!env.SESSION_SECRET) return json({ error: missingSecret('SESSION_SECRET') }, 500);

  let body;
  try { body = await request.json(); } catch { return json({ error: 'Invalid request body.' }, 400); }
  const email = String(body.email || '').trim().toLowerCase();
  const pass = String(body.password || '');

  const expectedEmail = String(env.AUTH_EMAIL).trim().toLowerCase();
  if (!email || !timingSafeEqualStr(email, expectedEmail)) {
    return json({ error: 'Invalid email or password.' }, 401);
  }
  if (!pass || !timingSafeEqualStr(pass, String(env.AUTH_PASS))) {
    return json({ error: 'Invalid email or password.' }, 401);
  }

  const token = await makeSession(env.SESSION_SECRET, email, TTL_MS);
  return json({ ok: true, email }, { status: 200, headers: { 'Set-Cookie': cookieHeader(token, TTL_MS / 1000, cookieSecure(request)) } });
}