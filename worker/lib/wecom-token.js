import { log } from "./log.js";

// 企业微信 access_token 缓存（Cache API，1.5h TTL，官方有效期 2h）
const CACHE_KEY = new Request("https://token-cache/wecom-access-token");
const TTL = 5400;

export async function getWecomToken(env) {
  const cache = caches.default;
  const cached = await cache.match(CACHE_KEY);
  if (cached) return cached.text();

  const resp = await fetch(
    `https://qyapi.weixin.qq.com/cgi-bin/gettoken?corpid=${env.WECOM_CORP_ID}&corpsecret=${env.WECOM_CORP_SECRET}`
  );
  const { access_token, errmsg } = await resp.json();
  if (!access_token) {
    log.error("wecom token fetch failed", { errmsg });
    throw new Error("获取企业微信 token 失败");
  }

  await cache.put(CACHE_KEY, new Response(access_token, {
    headers: { "Cache-Control": `max-age=${TTL}` },
  }));
  return access_token;
}
