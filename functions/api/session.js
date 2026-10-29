import { json, readSession } from '../_lib.js';

export async function onRequestGet(context) {
  const { request, env } = context;
  const cookie = request.headers.get('Cookie') || '';
  const session = await readSession(cookie, env.SESSION_SECRET);
  if (!session) return json({ authenticated: false }, 200);
  return json({ authenticated: true, email: session.email }, 200);
}