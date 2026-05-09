// 企业微信消息解密 — Web Crypto API (AES-256-CBC, PKCS#7)

/**
 * @typedef {{ message: string, corpId: string }} DecryptResult
 */

/**
 * 从 EncodingAESKey 导入 CryptoKey
 * @param {string} encodingAESKey - 43 字符 Base64url-like key
 * @returns {Promise<CryptoKey>}
 */
async function importKey(encodingAESKey) {
  // 企业微信的 EncodingAESKey 是 43 字符 + 补 "="，标准 Base64
  const raw = Uint8Array.from(atob(encodingAESKey + "="), c => c.charCodeAt(0));
  return crypto.subtle.importKey("raw", raw, { name: "AES-CBC" }, false, ["decrypt"]);
}

/**
 * 解密企业微信消息
 * @param {string} encrypted - Base64 编码的密文
 * @param {string} encodingAESKey - 43 字符密钥
 * @returns {Promise<DecryptResult>}
 */
export async function decrypt(encrypted, encodingAESKey) {
  const key = await importKey(encodingAESKey);
  const cipherBytes = Uint8Array.from(atob(encrypted), c => c.charCodeAt(0));

  // 前 16 字节是 IV
  const iv = cipherBytes.slice(0, 16);
  const data = cipherBytes.slice(16);

  const decrypted = await crypto.subtle.decrypt({ name: "AES-CBC", iv }, key, data);
  const buf = new Uint8Array(decrypted);

  // 去掉前 16 字节随机填充
  // 接下来 4 字节是消息长度（网络字节序）
  const msgLen = (buf[16] << 24) | (buf[17] << 16) | (buf[18] << 8) | buf[19];
  const message = new TextDecoder().decode(buf.slice(20, 20 + msgLen));
  const corpId = new TextDecoder().decode(buf.slice(20 + msgLen));

  return { message, corpId };
}

/**
 * 企业微信回调签名验证
 * @param {string} token - 回调 Token
 * @param {string} timestamp
 * @param {string} nonce
 * @param {string} encrypted - 加密消息体
 * @returns {Promise<string>} SHA-1 hex
 */
export async function sign(token, timestamp, nonce, encrypted) {
  const str = [token, timestamp, nonce, encrypted].sort().join("");
  const data = new TextEncoder().encode(str);
  const hash = await crypto.subtle.digest("SHA-1", data);
  return [...new Uint8Array(hash)].map(b => b.toString(16).padStart(2, "0")).join("");
}
