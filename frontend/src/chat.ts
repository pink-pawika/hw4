export type ChatProduct = {
  product_id: string
  name: string
  garment_type?: string
  price: number
  image_url: string
  description: string
  total_stock?: number | null
}

export type ChatResult = {
  message: string
  products: ChatProduct[]
}

export type StoredMessage = {
  id: number
  role: 'user' | 'assistant'
  content: string
  products: ChatProduct[]
}

export function productIdFromPath(pathname: string): string | null {
  const match = pathname.match(/^\/products\/([^/]+)$/)
  if (!match) return null
  return decodeURIComponent(match[1])
}

export async function fetchChatHistory(): Promise<StoredMessage[]> {
  const response = await fetch('/api/chat/history', { credentials: 'include' })
  if (!response.ok) return []
  const data = (await response.json().catch(() => [])) as StoredMessage[]
  return Array.isArray(data) ? data : []
}

export async function sendChatMessage(
  message: string,
  history: { role: 'user' | 'assistant'; content: string }[],
  pageProductId: string | null,
): Promise<ChatResult> {
  const response = await fetch('/api/chat', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    credentials: 'include',
    body: JSON.stringify({
      message,
      history,
      page_product_id: pageProductId,
    }),
  })
  const data = (await response.json().catch(() => ({}))) as {
    message?: string
    products?: ChatProduct[]
    detail?: string
  }
  if (!response.ok) {
    const detail = typeof data.detail === 'string' ? data.detail : ''
    throw new Error(detail || "The shop assistant couldn't answer.")
  }
  return {
    message: data.message ?? '',
    products: data.products ?? [],
  }
}
