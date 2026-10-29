import { readSession, json, LOGIN_HTML } from './_lib.js';

export async function onRequest(context) {
  const { request, env, next } = context;
  const url = new URL(request.url);
  const path = url.pathname;

  const publicPaths = ['/api/login', '/api/session', '/api/logout'];
  if (publicPaths.includes(path)) {
    return next();
  }

  const cookie = request.headers.get('Cookie') || '';
  const session = await readSession(cookie, env.SESSION_SECRET);
  if (session) {
    return next();
  }

  if (path === '/api/' || path.startsWith('/api/')) {
    return json({ error: 'Not authenticated' }, 401);
  }

  return new Response(LOGIN_HTML, {
    status: 401,
    headers: { 'content-type': 'text/html; charset=utf-8' },
  });
}