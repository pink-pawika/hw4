import type { ProductDetail, ProductSummary } from './types.ts'

async function readJson<T>(path: string): Promise<T> {
  const response = await fetch(path)
  if (!response.ok) {
    throw new Error(`Request failed (${response.status})`)
  }
  return response.json() as Promise<T>
}

export function fetchProducts(): Promise<ProductSummary[]> {
  return readJson('/api/products')
}

export function fetchProduct(productId: string): Promise<ProductDetail> {
  return readJson(`/api/products/${encodeURIComponent(productId)}`)
}

export function formatPrice(price: number): string {
  return new Intl.NumberFormat('en-US', {
    style: 'currency',
    currency: 'USD',
  }).format(price)
}
