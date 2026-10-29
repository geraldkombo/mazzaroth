import { json, clearCookieHeader, cookieSecure } from '../_lib.js';

export async function onRequestPost(context) {
  return json({ ok: true }, { status: 200, headers: { 'Set-Cookie': clearCookieHeader(cookieSecure(context.request)) } });
}