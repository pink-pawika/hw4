import { useEffect, useState } from 'react'
import { Link } from 'react-router-dom'
import { fetchProducts, formatPrice } from '../api.ts'
import { RACK_GROUPS, garmentGroup } from '../garments.ts'
import type { RackGroup } from '../garments.ts'
import { useMatches } from '../matches.tsx'
import type { ProductSummary } from '../types.ts'

type RackCard = {
  product_id: string
  name: string
  garment_type?: string
  description: string
  price: number
  image_url: string
  total_stock?: number | null
}

export default function ProductsPage() {
  const { query, products: matches, clearMatches } = useMatches()
  const [products, setProducts] = useState<ProductSummary[]>([])
  const [error, setError] = useState('')
  const [group, setGroup] = useState<RackGroup>('all')
  const showingMatches = matches.length > 0

  useEffect(() => {
    let active = true
    fetchProducts()
      .then((rows) => {
        if (active) setProducts(rows)
      })
      .catch(() => {
        if (active) setError("The catalogue didn't load. Start the shop backend and refresh.")
      })
    return () => {
      active = false
    }
  }, [])

  useEffect(() => {
    if (showingMatches) {
      document.querySelector('.main')?.scrollIntoView({ behavior: 'smooth', block: 'start' })
    }
  }, [showingMatches, query])

  const rack: RackCard[] = showingMatches ? matches : products
  const counts = RACK_GROUPS.map((item) => ({
    ...item,
    count: item.id === 'all' ? rack.length : rack.filter((product) => garmentGroup(product.garment_type) === item.id).length,
  }))
  const shown = group === 'all' ? rack : rack.filter((product) => garmentGroup(product.garment_type) === group)

  return (
    <section>
      {showingMatches ? (
        <>
          <p className="eyebrow">From your question</p>
          <div className="rack-heading">
            <h1>{matches.length === 1 ? '1 matching piece' : `${matches.length} matching pieces`}</h1>
            <button type="button" className="rack-clear" onClick={clearMatches}>
              Show the full rack
            </button>
          </div>
          <p className="lede">“{query}”</p>
        </>
      ) : (
        <>
          <p className="eyebrow">Products</p>
          <h1>The rack</h1>
          <p className="lede">Name, price, and a short note. Open a piece for sizes and what's left.</p>
        </>
      )}
      <div className="rack-filters" role="group" aria-label="Filter the rack">
        {counts.map((item) => (
          <button
            key={item.id}
            type="button"
            className={group === item.id ? 'rack-filter active' : 'rack-filter'}
            aria-pressed={group === item.id}
            onClick={() => setGroup(item.id)}
          >
            {item.label}
            <span>{item.count}</span>
          </button>
        ))}
      </div>
      {error && !showingMatches && <p className="status-error">{error}</p>}
      {!error && !showingMatches && products.length === 0 && <p className="status-muted">Loading the rack…</p>}
      {shown.length === 0 && rack.length > 0 && <p className="status-muted">Nothing in this group.</p>}
      <div className="product-grid">
        {shown.map((product) => (
          <Link key={product.product_id} className="product-card" to={`/products/${product.product_id}`}>
            <div className="product-photo">
              <img src={product.image_url} alt={product.name} />
              {product.total_stock === 0 && <span className="sold-out-badge">Sold out</span>}
            </div>
            <div className="product-copy">
              <h2>{product.name}</h2>
              <p className="price">{formatPrice(product.price)}</p>
              <p className="short-description">{product.description}</p>
            </div>
          </Link>
        ))}
      </div>
    </section>
  )
}
