export type ProductSummary = {
  product_id: string
  name: string
  garment_type: string
  description: string
  price: number
  image_url: string
  total_stock: number
}

export type ProductSize = {
  size: string
  quantity: number
}

export type ProductDetail = ProductSummary & {
  garment_type: string
  colors: string[]
  sizes: ProductSize[]
}
