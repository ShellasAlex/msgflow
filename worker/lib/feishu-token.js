import { log } from "./log.js";

// 飞书 tenant_access_token 缓存（Cache API，2h TTL）
const CACHE_KEY = new Request("https://token-cache/feishu-tenant-token");
const TTL = 7200; // 2 小时

export async function getFeishuToken(env) {
  const cache = caches.default;
  const cached = await cache.match(CACHE_KEY);
  if (cached) return cached.text();

  const resp = await fetch("https://open.feishu.cn/open-apis/auth/v3/tenant_access_token/internal", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ app_id: env.FEISHU_APP_ID, app_secret: env.FEISHU_APP_SECRET }),
  });
  const { tenant_access_token } = await resp.json();
  if (!tenant_access_token) {
    log.error("feishu token fetch failed");
    throw new Error("获取飞书 token 失败");
  }

  await cache.put(CACHE_KEY, new Response(tenant_access_token, {
    headers: { "Cache-Control": `max-age=${TTL}` },
  }));
  return tenant_access_token;
}
