import { decrypt, sign } from "../lib/crypto.js";
import { parseCommand, HELP_TEXT } from "../lib/command.js";
import { triggerWorkflow } from "../lib/github.js";
import { getWecomToken } from "../lib/wecom-token.js";
import { checkRateLimit } from "../lib/rate-limit.js";
import { log, setContext } from "../lib/log.js";

// GET: 企业微信验证回调 URL
export async function handleWecomVerify(request, env) {
  const url = new URL(request.url);
  const msg_signature = url.searchParams.get("msg_signature");
  const timestamp = url.searchParams.get("timestamp");
  const nonce = url.searchParams.get("nonce");
  const echostr = url.searchParams.get("echostr");

  const computed = await sign(env.WECOM_TOKEN, timestamp, nonce, echostr);
  if (computed !== msg_signature) {
    log.warn("wecom verify signature mismatch");
    return new Response("Forbidden", { status: 403 });
  }

  const { message } = await decrypt(echostr, env.WECOM_ENCODING_AES_KEY);
  return new Response(message);
}

// POST: 接收企业微信消息
export async function handleWecom(request, env) {
  const url = new URL(request.url);
  const msg_signature = url.searchParams.get("msg_signature");
  const timestamp = url.searchParams.get("timestamp");
  const nonce = url.searchParams.get("nonce");

  const xml = await request.text();
  const encrypted = extractXml(xml, "Encrypt");
  if (!encrypted) return new Response("OK");

  // 验签
  const computed = await sign(env.WECOM_TOKEN, timestamp, nonce, encrypted);
  if (computed !== msg_signature) {
    log.warn("wecom message signature mismatch");
    return new Response("Forbidden", { status: 403 });
  }

  // 解密
  const { message, corpId } = await decrypt(encrypted, env.WECOM_ENCODING_AES_KEY);
  if (corpId !== env.WECOM_CORP_ID) return new Response("Forbidden", { status: 403 });

  // 解析 XML 消息
  const msgType = extractXml(message, "MsgType");
  if (msgType !== "text") return new Response("OK");

  const content = extractXml(message, "Content");
  const fromUser = extractXml(message, "FromUserName");
  const agentId = extractXml(message, "AgentID");
  if (!content || !fromUser || !agentId) return new Response("OK");
  setContext({ channel: "wecom", userId: fromUser });

  const command = parseCommand(content);
  if (!command || command.action === "help") {
    await sendWecom(env, fromUser, agentId, HELP_TEXT);
    return new Response("OK");
  }

  await sendWecom(env, fromUser, agentId, `收到，正在处理... ⏳\n${command.action}: ${command.target || ""}`);
  if (!await checkRateLimit("wecom", fromUser)) {
    await sendWecom(env, fromUser, agentId, "⚠️ 操作太频繁，请稍后再试");
    return new Response("OK");
  }
  const { ok, error } = await triggerWorkflow(env, command, "wecom", `${fromUser}|${agentId}`);
  if (!ok) {
    log.warn("wecom trigger failed", { fromUser, action: command.action, error });
    await sendWecom(env, fromUser, agentId, `⚠️ 触发失败: ${error}`);
  }
  return new Response("OK");
}

// 主动发送消息
export async function sendWecom(env, userId, agentId, text) {
  const access_token = await getWecomToken(env);
  const resp = await fetch(`https://qyapi.weixin.qq.com/cgi-bin/message/send?access_token=${access_token}`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      touser: userId,
      msgtype: "text",
      agentid: Number(agentId),
      text: { content: text.substring(0, 2048) },
    }),
  });
  if (!resp.ok) log.warn("sendWecom failed", { status: resp.status, userId });
}

/**
 * 简易 XML 标签提取（企业微信消息格式固定，无需完整 XML 解析器）
 * @param {string} xml
 * @param {string} tag
 * @returns {string|null}
 */
function extractXml(xml, tag) {
  const match = xml.match(new RegExp(`<${tag}><!\\[CDATA\\[([\\s\\S]*?)\\]\\]></${tag}>`))
    || xml.match(new RegExp(`<${tag}>([^<]*)</${tag}>`));
  return match ? match[1] : null;
}
