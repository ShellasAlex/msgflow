// 简易速率限制 — Cache API，每用户每分钟最多 5 次 workflow 触发
const MAX_PER_MINUTE = 5;

export async function checkRateLimit(channel, userId) {
  const key = new Request(`https://ratelimit/${channel}:${userId}`);
  const cache = caches.default;
  const cached = await cache.match(key);
  const count = cached ? parseInt(await cached.text()) : 0;

  if (count >= MAX_PER_MINUTE) return false;

  await cache.put(key, new Response(String(count + 1), {
    headers: { "Cache-Control": "max-age=60" },
  }));
  return true;
}
