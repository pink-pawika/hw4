import { createContext, useContext, useMemo, useState } from 'react'
import type { ReactNode } from 'react'
import type { ChatProduct } from './chat.ts'

type MatchState = {
  query: string
  products: ChatProduct[]
  setMatches: (query: string, products: ChatProduct[]) => void
  clearMatches: () => void
}

const MatchContext = createContext<MatchState | null>(null)

export function MatchProvider({ children }: { children: ReactNode }) {
  const [query, setQuery] = useState('')
  const [products, setProducts] = useState<ChatProduct[]>([])
  const value = useMemo(
    () => ({
      query,
      products,
      setMatches: (nextQuery: string, nextProducts: ChatProduct[]) => {
        setQuery(nextQuery.trim())
        setProducts(nextProducts)
      },
      clearMatches: () => {
        setQuery('')
        setProducts([])
      },
    }),
    [query, products],
  )
  return <MatchContext.Provider value={value}>{children}</MatchContext.Provider>
}

export function useMatches(): MatchState {
  const value = useContext(MatchContext)
  if (!value) {
    throw new Error('Shop matches are only available inside the site layout.')
  }
  return value
}
