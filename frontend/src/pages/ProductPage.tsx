import { useEffect, useState } from 'react'
import { Link, useParams } from 'react-router-dom'
import { fetchProduct, formatPrice } from '../api.ts'
import type { ProductDetail } from '../types.ts'

export default function ProductPage() {
  const { productId } = useParams()
  const [product, setProduct] = useState<ProductDetail | null>(null)
  const [error, setError] = useState('')

  useEffect(() => {
    if (!productId) return
    let active = true
    setProduct(null)
    setError('')
    fetchProduct(productId)
      .then((row) => {
        if (active) setProduct(row)
      })
      .catch(() => {
        if (active) setError("That piece isn't on the rack.")
      })
    return () => {
      active = false
    }
  }, [productId])

  if (error) {
    return (
      <article className="prose">
        <p className="status-error">{error}</p>
        <Link className="text-link" to="/products">
          Back to products
        </Link>
      </article>
    )
  }

  if (!product) {
    return <p className="status-muted">Loading this piece…</p>
  }

  return (
    <article>
      <Link className="text-link" to="/products">
        Back to products
      </Link>
      <div className="product-detail">
        <div className="product-photo large">
          <img src={product.image_url} alt={product.name} />
          {product.total_stock === 0 && <span className="sold-out-badge">Sold out</span>}
        </div>
        <div className="product-text">
          <p className="eyebrow">{product.garment_type}</p>
          <h1>{product.name}</h1>
          <p className="price large">{formatPrice(product.price)}</p>
          <p className="description">{product.description}</p>
          {product.colors.length > 0 && (
            <p className="colors">Colors: {product.colors.join(', ')}</p>
          )}
          <h2>Sizes</h2>
          <ul className="size-list">
            {product.sizes.map((size) => (
              <li key={size.size}>
                <span>{size.size}</span>
                {size.quantity === 0 ? (
                  <span className="sold-out-badge inline">Sold out</span>
                ) : (
                  <span>{size.quantity} in stock</span>
                )}
              </li>
            ))}
          </ul>
        </div>
      </div>
    </article>
  )
}
