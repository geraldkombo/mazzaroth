const enc = new TextEncoder();

function b64url(s) {
  return btoa(unescape(encodeURIComponent(s)))
    .replace(/\+/g, '-')
    .replace(/\//g, '_')
    .replace(/=+$/, '');
}

function fromB64url(s) {
  const pad = s.length % 4 === 0 ? '' : '='.repeat(4 - (s.length % 4));
  return decodeURIComponent(escape(atob(s.replace(/-/g, '+').replace(/_/g, '/') + pad)));
}

function toHex(buf) {
  return [...new Uint8Array(buf)].map((b) => b.toString(16).padStart(2, '0')).join('');
}

export async function hmacHex(key, data) {
  const k = await crypto.subtle.importKey('raw', enc.encode(key), { name: 'HMAC', hash: 'SHA-256' }, false, ['sign']);
  const sig = await crypto.subtle.sign('HMAC', k, enc.encode(data));
  return toHex(sig);
}

export async function makeSession(secret, email, ttlMs) {
  const exp = Date.now() + ttlMs;
  const body = b64url(JSON.stringify({ e: email, x: exp }));
  const sig = await hmacHex(secret, body);
  return `m1.${body}.${sig}`;
}

export async function readSession(cookie, secret) {
  if (!cookie || !secret) return null;
  const parts = cookie.split(/[. ]+/).filter(Boolean);
  if (!cookie.startsWith('mazz_auth=')) return null;
  const value = cookie.slice('mazz_auth='.length).split(';')[0].trim();
  const bits = value.split('.');
  if (bits.length !== 3 || bits[0] !== 'm1') return null;
  const [, body, sig] = bits;
  const expect = await hmacHex(secret, body);
  if (sig !== expect) return null;
  let payload;
  try { payload = JSON.parse(fromB64url(body)); } catch { return null; }
  if (!payload.e || typeof payload.x !== 'number' || payload.x < Date.now()) return null;
  return { email: payload.e, exp: payload.x };
}

export function cookieHeader(token, maxAgeSec, secure = true) {
  const sec = secure ? '; Secure' : '';
  return `mazz_auth=${token}; Path=/; HttpOnly; SameSite=Lax${sec}; Max-Age=${maxAgeSec}`;
}

export function clearCookieHeader(secure = true) {
  const sec = secure ? '; Secure' : '';
  return `mazz_auth=; Path=/; HttpOnly; SameSite=Lax${sec}; Max-Age=0`;
}

export function cookieSecure(request) {
  try {
    const h = new URL(request.url).hostname;
    return !(h === 'localhost' || h === '127.0.0.1' || h === '::1');
  } catch {
    return true;
  }
}

export function json(data, statusOrOptions) {
  const opts = typeof statusOrOptions === 'object' && statusOrOptions !== null ? statusOrOptions : {};
  const status = typeof statusOrOptions === 'number' ? statusOrOptions : opts.status || 200;
  return new Response(JSON.stringify(data), {
    status,
    headers: { 'content-type': 'application/json; charset=utf-8', ...(opts.headers || {}) },
  });
}

export function timingSafeEqualStr(a, b) {
  if (typeof a !== 'string' || typeof b !== 'string') return false;
  const la = a.length, lb = b.length;
  let diff = la ^ lb;
  const n = Math.max(la, lb);
  for (let i = 0; i < n; i++) {
    diff |= (a.charCodeAt(i) || 0) ^ (b.charCodeAt(i) || 0);
  }
  return diff === 0;
}

export function missingSecret(name) {
  return `Missing secret: ${name}. Set it with: npx wrangler pages secret put ${name}`;
}

export const LOGIN_HTML = `<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>MAZZAROTH — Sign in</title>
<style>
*{margin:0;padding:0;box-sizing:border-box}
body{background:#06060c;color:#c8c8d4;font-family:Inter,-apple-system,sans-serif;min-height:100vh;display:flex;align-items:center;justify-content:center;padding:20px}
#box{max-width:360px;width:100%}
h1{color:#fff;font-size:24px;letter-spacing:-.3px;text-align:center;margin-bottom:2px}
p.sub{color:#666680;font-size:11px;text-align:center;margin-bottom:20px}
#card{background:#0c0c18;border:1px solid #1a1a2e;border-radius:12px;padding:22px}
label{display:block;font-size:10px;text-transform:uppercase;letter-spacing:.6px;color:#666680;margin:12px 0 4px}
input{width:100%;background:#08081a;border:1px solid #1a1a2e;color:#fff;padding:11px;border-radius:7px;font-size:14px;outline:none}
input:focus{border-color:#7c5cfc}
button{width:100%;margin-top:18px;background:#7c5cfc;color:#fff;border:none;padding:12px;border-radius:7px;font-size:14px;font-weight:600;cursor:pointer}
button:hover{opacity:.88}
#err{color:#ff4444;font-size:11px;margin-top:10px;min-height:16px;text-align:center}
.hint{font-size:9px;color:#666680;text-align:center;margin-top:14px;line-height:1.6}
</style>
</head>
<body>
<div id="box">
  <h1>MAZZAROTH</h1>
  <p class="sub">Daily Oracle &middot; Private</p>
  <div id="card">
    <label for="email">Email</label>
    <input id="email" type="email" autocomplete="username" placeholder="you@example.com">
    <label for="pass">Password</label>
    <input id="pass" type="password" autocomplete="current-password" placeholder="••••••••">
    <button onclick="login()">Sign in</button>
    <div id="err"></div>
  </div>
  <div class="hint">Personal app. Access is limited to your email.<br>If you forgot the password, reset it in Cloudflare secrets.</div>
</div>
<script>
async function login(){
  const err=document.getElementById('err');
  err.textContent='';
  const email=document.getElementById('email').value.trim();
  const pass=document.getElementById('pass').value;
  if(!email||!pass){err.textContent='Enter email and password.';return;}
  const r=await fetch('/api/login',{method:'POST',headers:{'content-type':'application/json'},body:JSON.stringify({email,password:pass})});
  if(r.ok){location.href='/';return;}
  const d=await r.json().catch(()=>({}));
  err.textContent=d.error||'Sign-in failed: '+r.status;
}
document.addEventListener('keydown',e=>{if(e.key==='Enter')login();});
</script>
</body>
</html>`;

export const THRESHOLDS = { peak: 11675, vhigh: 10806, high: 9480 };

export function levelOf(score) {
  if (score >= THRESHOLDS.peak) return 'PEAK';
  if (score >= THRESHOLDS.vhigh) return 'VERY HIGH';
  if (score >= THRESHOLDS.high) return 'HIGH';
  return 'NORMAL';
}