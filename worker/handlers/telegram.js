import { parseCommand, HELP_TEXT } from "../lib/command.js";
import { triggerWorkflow } from "../lib/github.js";
import { checkRateLimit } from "../lib/rate-limit.js";
import { log, setContext } from "../lib/log.js";

export async function handleTelegram(request, env) {
  // 验证请求来自 Telegram（secret_token 在 /setup 时设置）
  if (env.CALLBACK_SECRET && request.headers.get("x-telegram-bot-api-secret-token") !== env.CALLBACK_SECRET) {
    return new Response("Forbidden", { status: 403 });
  }

  const body = await request.json();
  const message = body.message;
  if (!message || !message.text) return new Response("OK");

  const chatId = message.chat.id;
  setContext({ channel: "telegram", userId: String(chatId) });
  const command = parseCommand(message.text.trim());

  if (!command || command.action === "help") {
    await sendTelegram(env, chatId, HELP_TEXT);
    return new Response("OK");
  }

  await sendTelegram(env, chatId, `收到，正在处理... ⏳\n${command.action}: ${command.target || ""}`);
  if (!await checkRateLimit("telegram", chatId)) {
    await sendTelegram(env, chatId, "⚠️ 操作太频繁，请稍后再试");
    return new Response("OK");
  }
  const { ok, error } = await triggerWorkflow(env, command, "telegram", chatId);
  if (!ok) {
    log.warn("telegram trigger failed", { chatId, action: command.action, error });
    await sendTelegram(env, chatId, `⚠️ 触发失败: ${error}`);
  }
  return new Response("OK");
}

export async function sendTelegram(env, chatId, text) {
  for (let i = 0; i < text.length; i += 4096) {
    const resp = await fetch(`https://api.telegram.org/bot${env.TELEGRAM_BOT_TOKEN}/sendMessage`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ chat_id: chatId, text: text.substring(i, i + 4096) }),
    });
    if (!resp.ok) log.warn("sendTelegram failed", { status: resp.status, chatId });
  }
}
