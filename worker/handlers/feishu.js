import { parseCommand, HELP_TEXT } from "../lib/command.js";
import { triggerWorkflow } from "../lib/github.js";
import { getFeishuToken } from "../lib/feishu-token.js";
import { checkRateLimit } from "../lib/rate-limit.js";
import { log, setContext } from "../lib/log.js";

export async function handleFeishu(request, env) {
  const body = await request.json();

  // URL 验证（飞书首次配置回调时）
  if (body.type === "url_verification") {
    return Response.json({ challenge: body.challenge });
  }

  const header = body.header;
  if (!header || header.token !== env.FEISHU_VERIFICATION_TOKEN) {
    return new Response("Unauthorized", { status: 401 });
  }

  // 事件去重
  const eventId = header.event_id;
  if (eventId) {
    const req = new Request(`https://dedup/feishu_event:${eventId}`);
    if (await caches.default.match(req)) return new Response("OK");
    await caches.default.put(req, new Response("1", {
      headers: { "Cache-Control": "max-age=300" },
    }));
  }

  if (header.event_type !== "im.message.receive_v1") return new Response("OK");

  const message = body.event.message;
  if (message.message_type !== "text") return new Response("OK");

  let text;
  try {
    text = JSON.parse(message.content).text.trim();
  } catch {
    return new Response("OK");
  }
  const chatId = message.chat_id;
  setContext({ channel: "feishu", userId: chatId });
  const command = parseCommand(text);

  if (!command || command.action === "help") {
    await sendFeishu(env, chatId, HELP_TEXT);
    return new Response("OK");
  }

  await sendFeishu(env, chatId, `收到，正在处理... ⏳\n${command.action}: ${command.target || ""}`);
  if (!await checkRateLimit("feishu", chatId)) {
    await sendFeishu(env, chatId, "⚠️ 操作太频繁，请稍后再试");
    return new Response("OK");
  }
  const { ok, error } = await triggerWorkflow(env, command, "feishu", chatId);
  if (!ok) {
    log.warn("feishu trigger failed", { chatId, action: command.action, error });
    await sendFeishu(env, chatId, `⚠️ 触发失败: ${error}`);
  }
  return new Response("OK");
}

export async function sendFeishu(env, chatId, text) {
  const token = await getFeishuToken(env);
  const resp = await fetch("https://open.feishu.cn/open-apis/im/v1/messages?receive_id_type=chat_id", {
    method: "POST",
    headers: { Authorization: `Bearer ${token}`, "Content-Type": "application/json" },
    body: JSON.stringify({ receive_id: chatId, msg_type: "text", content: JSON.stringify({ text }) }),
  });
  if (!resp.ok) log.warn("sendFeishu failed", { status: resp.status, chatId });
}
