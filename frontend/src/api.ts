/**
 * 学生宿舍管理系统 - API 请求封装模块
 * 提供带 Bearer 令牌的通用 fetch 请求封装，统一处理错误。
 */

/** API 基础路径，可通过环境变量 VITE_API_BASE_URL 自定义 */
const API_BASE = import.meta.env.VITE_API_BASE_URL ?? ''

/**
 * 发起 API 请求的通用函数。
 *
 * @param path  请求路径（如 "/api/auth/login"）
 * @param token Bearer 认证令牌
 * @param options 原生 RequestInit 配置
 * @returns 解析后的 JSON 数据
 * @throws 当请求失败时抛出包含错误详情的 Error
 */
export async function apiRequest<T>(
  path: string,
  token: string,
  options: RequestInit = {},
): Promise<T> {
  const headers = new Headers(options.headers)
  // 非 FormData 请求体自动设置 Content-Type 为 JSON
  if (options.body && !(options.body instanceof FormData)) {
    headers.set('Content-Type', 'application/json')
  }
  // 携带 Bearer 令牌
  if (token) {
    headers.set('Authorization', `Bearer ${token}`)
  }

  const response = await fetch(`${API_BASE}${path}`, {
    ...options,
    headers,
  })
  const text = await response.text()
  const data = text ? JSON.parse(text) : null

  // 响应非 OK 时提取错误详情并抛出
  if (!response.ok) {
    const detail = data?.detail
    throw new Error(Array.isArray(detail) ? detail.map((item) => item.msg).join('；') : detail || response.statusText)
  }

  return data as T
}
