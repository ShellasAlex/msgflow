const SENSITIVE_KEYS = ["nullclaw_api_key", "mowen_api_key", "unsplash_key", "llmwiki_token"];
const NON_SENSITIVE_KEYS = ["nullclaw_base_url", "nullclaw_model", "wiki_repo", "task_timeout"];

function mask(val) {
  if (!val || val.length <= 4) return "****";
  return val.substring(0, 4) + "****";
}

export async function getConfig(env) {
  const raw = await env.MSGFLOW_CONFIG.get("config");
  return raw ? JSON.parse(raw) : {};
}

export async function setConfig(env, data) {
  const current = await getConfig(env);
  // 保留未修改的敏感值（前端传回 mask 值时不覆盖）
  for (const key of SENSITIVE_KEYS) {
    if (data[key] && data[key].includes("****")) delete data[key];
  }
  const merged = { ...current, ...data };
  await env.MSGFLOW_CONFIG.put("config", JSON.stringify(merged));
  return merged;
}

export function getMaskedConfig(config) {
  const out = {};
  for (const key of [...SENSITIVE_KEYS, ...NON_SENSITIVE_KEYS]) {
    if (config[key] === undefined) continue;
    out[key] = SENSITIVE_KEYS.includes(key) ? mask(config[key]) : config[key];
  }
  return out;
}

export function getSensitiveConfig(config) {
  const out = {};
  for (const key of SENSITIVE_KEYS) {
    if (config[key]) out[key] = config[key];
  }
  return out;
}

export function getNonSensitiveConfig(config) {
  const out = {};
  for (const key of NON_SENSITIVE_KEYS) {
    if (config[key]) out[key] = config[key];
  }
  return out;
}
