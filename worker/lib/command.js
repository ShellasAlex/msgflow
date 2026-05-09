/**
 * @typedef {{ action: string, target?: string, style?: string, skill?: string }} Command
 */

/**
 * 通用指令解析
 * @param {string} text - 用户消息文本
 * @returns {Command|null}
 */
export function parseCommand(text) {
  if (!text) return null;
  text = text.replace(/^\/start\s*/, "").trim();
  if (!text) return null;

  if (/^(?:帮助|help|指令|命令|\?)$/i.test(text)) return { action: "help" };

  const ingestMatch = text.match(/^(?:摄入|ingest)\s+(https?:\/\/\S+)$/i);
  if (ingestMatch) return { action: "ingest", target: ingestMatch[1] };

  const queryMatch = text.match(/^(?:查询|query)\s+(.+)$/i);
  if (queryMatch) return { action: "query", target: queryMatch[1] };

  const distillMatch = text.match(/^(?:蒸馏|distill)\s+(.+)$/i);
  if (distillMatch) return { action: "distill", target: distillMatch[1] };

  const publishMatch = text.match(/^(?:发布|publish)\s+(.+)$/i);
  if (publishMatch) {
    const target = publishMatch[1].trim();
    // 发布飞书 / 发布墨问 带渠道指定
    const channelMatch = target.match(/^(?:飞书|feishu)\s+(.+)$/i);
    if (channelMatch) return { action: "publish_feishu", target: channelMatch[1].trim() };
    const mowenMatch = target.match(/^(?:墨问|mowen)\s+(.+)$/i);
    if (mowenMatch) return { action: "publish", target: mowenMatch[1].trim() };
    return { action: "publish", target };
  }

  if (/^(?:健康检查|lint)$/i.test(text)) return { action: "lint", target: "full" };
  if (/^(?:待发布|pending)$/i.test(text)) return { action: "pending", target: "list" };

  const rewriteMatch = text.match(/^(?:改写|rewrite)\s+(鲁迅|马三立|徐志摩|lu-xun|ma-sanli|xu-zhimo)\s+(.+)$/i);
  if (rewriteMatch) {
    const styleMap = { "鲁迅": "lu-xun", "马三立": "ma-sanli", "徐志摩": "xu-zhimo" };
    return { action: "rewrite", style: styleMap[rewriteMatch[1]] || rewriteMatch[1], target: rewriteMatch[2].trim() };
  }

  const urlMatch = text.match(/(https?:\/\/\S+)/i);
  if (urlMatch) return { action: "fetch", target: urlMatch[1] };

  const skillMatch = text.match(/^skill:(\S+)\s+(.+)$/i);
  if (skillMatch) return { action: "skill", skill: skillMatch[1], target: skillMatch[2] };

  return null;
}

export const HELP_TEXT = `支持的指令：
• 发 URL → 抓取为 Markdown
• 摄入 <URL> → 抓取并存入知识库
• 查询 <问题> → 基于知识库回答
• 改写 鲁迅/马三立/徐志摩 <URL> → 风格改写+自动发布
• 待发布 → 查看未上传的文件
• 发布 <文件路径> → 发布到默认渠道
• 发布 飞书 <标题> → 发布到飞书文档
• 发布 墨问 <文件路径> → 发布到墨问
• 蒸馏 <人名> → 生成人物思维 Skill
• 健康检查 → 检查知识库一致性
• skill:名称 <消息> → 执行任意 skill`;
