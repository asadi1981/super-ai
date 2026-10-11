const corsHeaders = (origin, env) => {
  const allowed = (env.SITE_ORIGIN || '').split(',').map(x => x.trim()).filter(Boolean);
  const permitted = allowed.includes(origin) ? origin : 'null';
  return {'Access-Control-Allow-Origin': permitted, 'Access-Control-Allow-Methods':'GET, POST, OPTIONS', 'Access-Control-Allow-Headers':'Content-Type', 'Vary':'Origin'};
};
export default {
  async fetch(request, env) {
    const url = new URL(request.url);
    const origin = request.headers.get('Origin') || '';
    const cors = corsHeaders(origin, env);
    const respond = (data, status=200) => new Response(JSON.stringify(data), {status, headers:{'Content-Type':'application/json; charset=utf-8', ...cors}});
    if (request.method === 'OPTIONS') return new Response(null,{status:204,headers:cors});
    if (url.pathname === '/health' && request.method === 'GET') return respond({status:'ok', service:'SUPER AI gateway'});
    if (url.pathname !== '/api/chat' || request.method !== 'POST') return respond({error:'Not found'},404);
    if (!origin || cors['Access-Control-Allow-Origin'] === 'null') return respond({error:'Origin not allowed'},403);
    if (!env.OPENROUTER_API_KEY) return respond({error:'Server API key is not configured'},500);
    try {
      const body = await request.json();
      if (!Array.isArray(body.messages) || body.messages.length < 1) return respond({error:'messages is required'},400);
      const messages = body.messages.slice(-20).map(m => ({role: ['user','assistant'].includes(m.role) ? m.role : 'user', content: String(m.content || '').slice(0,12000)}));
      messages.unshift({role:'system',content:'تو دستیار هوشمند SUPER AI هستی. به زبان کاربر، روشن، دقیق و مفید پاسخ بده. اگر چیزی را نمی‌دانی صادقانه بگو و ادعای دسترسی به ابزارهایی که فعال نیستند نکن.'});
      const upstream = await fetch('https://openrouter.ai/api/v1/chat/completions', {
        method:'POST', headers:{'Authorization':`Bearer ${env.OPENROUTER_API_KEY}`,'Content-Type':'application/json','HTTP-Referer':env.SITE_ORIGIN || 'https://github.com','X-Title':'SUPER AI'},
        body:JSON.stringify({model: body.model || env.DEFAULT_MODEL || 'openrouter/free', messages, temperature:0.7})
      });
      const result = await upstream.json();
      if (!upstream.ok) return respond({error:result.error?.message || `Provider error ${upstream.status}`},upstream.status);
      return respond(result);
    } catch (e) { return respond({error:e.message || 'Unexpected server error'},500); }
  }
};
