import { getConfig, setConfig, getMaskedConfig, getSensitiveConfig } from "../lib/config.js";

function timingSafeEqual(a, b) {
  if (a.length !== b.length) return false;
  let result = 0;
  for (let i = 0; i < a.length; i++) result |= a.charCodeAt(i) ^ b.charCodeAt(i);
  return result === 0;
}

function checkAdmin(request, env) {
  const url = new URL(request.url);
  const token = url.searchParams.get("token") ||
    (request.headers.get("Authorization") || "").replace("Bearer ", "");
  return token && timingSafeEqual(token, env.ADMIN_TOKEN || "");
}

export async function handleAdmin(request, env) {
  if (!checkAdmin(request, env)) return new Response("Forbidden", { status: 403 });
  return new Response(ADMIN_HTML, { headers: { "Content-Type": "text/html; charset=utf-8" } });
}

export async function handleAdminConfig(request, env) {
  if (!checkAdmin(request, env)) return new Response("Forbidden", { status: 403 });
  const json = (data) => new Response(JSON.stringify(data), { headers: { "Content-Type": "application/json" } });

  if (request.method === "GET") {
    const config = await getConfig(env);
    return json(getMaskedConfig(config));
  }
  if (request.method === "POST") {
    const body = await request.json();
    await setConfig(env, body);
    const config = await getConfig(env);
    return json(getMaskedConfig(config));
  }
  return new Response("Method Not Allowed", { status: 405 });
}

export async function handleInternalConfig(request, env) {
  if (request.method !== "POST") return new Response("Method Not Allowed", { status: 405 });
  const body = await request.json();
  if (!body.secret || !timingSafeEqual(body.secret, env.CALLBACK_SECRET || "")) {
    return new Response("Unauthorized", { status: 401 });
  }
  const config = await getConfig(env);
  return new Response(JSON.stringify(getSensitiveConfig(config)), {
    headers: { "Content-Type": "application/json" },
  });
}

const ADMIN_HTML = `<!DOCTYPE html>
<html lang="zh-CN"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>msgflow 配置管理</title>
<style>
*{box-sizing:border-box;margin:0;padding:0}
body{font-family:system-ui,sans-serif;background:#f5f5f5;padding:2rem;max-width:600px;margin:0 auto}
h1{font-size:1.4rem;margin-bottom:1.5rem;color:#333}
.section{background:#fff;border-radius:8px;padding:1.2rem;margin-bottom:1rem;box-shadow:0 1px 3px rgba(0,0,0,.1)}
.section h2{font-size:1rem;margin-bottom:.8rem;color:#555}
label{display:block;font-size:.85rem;color:#333;margin-bottom:.1rem;margin-top:.8rem;font-weight:500}
.desc{font-size:.75rem;color:#888;margin-bottom:.3rem}
input{width:100%;padding:.5rem;border:1px solid #ddd;border-radius:4px;font-size:.9rem}
button{margin-top:1.2rem;padding:.6rem 1.5rem;background:#2563eb;color:#fff;border:none;border-radius:6px;font-size:1rem;cursor:pointer}
button:hover{background:#1d4ed8}
.msg{margin-top:.8rem;font-size:.85rem;color:#16a34a}
.err{color:#dc2626}
</style></head><body>
<h1>⚙️ msgflow 配置管理</h1>
<p style="font-size:.85rem;color:#666;margin-bottom:1rem">不知道怎么填？<a href="https://github.com/ohwiki/msgflow/blob/main/docs/admin-config-guide.md" target="_blank" style="color:#2563eb">查看配置指南</a></p>
<div class="section"><h2>🤖 AI 配置</h2>
<label>API Key</label><div class="desc">AI 模型的密钥，用于调用大模型执行任务（如小米 MiMo、OpenAI 等）</div><input id="nullclaw_api_key" placeholder="sk-...">
<label>Base URL</label><div class="desc">AI 模型 API 的接口地址，不同提供商地址不同</div><input id="nullclaw_base_url" placeholder="https://api.example.com/v1">
<label>Model</label><div class="desc">使用的模型名称，决定 AI 的能力和成本</div><input id="nullclaw_model" placeholder="mimo-v2.5-pro">
</div>
<div class="section"><h2>📦 集成配置</h2>
<label>墨问 API Key</label><div class="desc">墨问写作平台的密钥，用于自动发布改写后的文章</div><input id="mowen_api_key" placeholder="mk-...">
<label>Unsplash Key</label><div class="desc">Unsplash 图片平台的 Access Key，用于自动获取文章封面图</div><input id="unsplash_key" placeholder="Access Key">
<label>Wiki Repo</label><div class="desc">知识库 GitHub 仓库地址（格式：用户名/仓库名），用于存储和查询知识</div><input id="wiki_repo" placeholder="user/repo">
<label>Wiki Token</label><div class="desc">访问私有知识库仓库的 GitHub Personal Access Token</div><input id="llmwiki_token" placeholder="ghp_...">
<label>任务超时(秒)</label><div class="desc">AI 执行单个任务的最长等待时间，蒸馏等复杂任务建议设为 1800</div><input id="task_timeout" type="number" placeholder="600">
</div>
<button onclick="save()">💾 保存</button>
<div id="msg" class="msg"></div>
<script>
const token=new URLSearchParams(location.search).get('token');
const fields=['nullclaw_api_key','nullclaw_base_url','nullclaw_model','mowen_api_key','unsplash_key','wiki_repo','llmwiki_token','task_timeout'];
const h={'Authorization':'Bearer '+token,'Content-Type':'application/json'};

async function load(){
  const r=await fetch('/admin/config',{headers:h});
  if(!r.ok)return;
  const d=await r.json();
  fields.forEach(f=>{if(d[f]!==undefined)document.getElementById(f).value=d[f]});
}

async function save(){
  const data={};
  fields.forEach(f=>{const v=document.getElementById(f).value;if(v)data[f]=f==='task_timeout'?Number(v):v});
  const r=await fetch('/admin/config',{method:'POST',headers:h,body:JSON.stringify(data)});
  const el=document.getElementById('msg');
  if(r.ok){el.className='msg';el.textContent='✅ 已保存（下次消息触发时生效）'}
  else{el.className='msg err';el.textContent='❌ 保存失败: '+r.status}
}
load();
</script></body></html>`;
