import { useEffect, useRef, useState } from 'react'
import type { FormEvent } from 'react'
import { Link, useLocation, useNavigate } from 'react-router-dom'
import { fetchChatHistory, productIdFromPath, sendChatMessage } from '../chat.ts'
import type { ChatProduct } from '../chat.ts'
import { fetchProduct, formatPrice } from '../api.ts'
import { useAuth } from '../auth.tsx'
import { useMatches } from '../matches.tsx'

type ChatMessage = {
  id: number
  role: 'user' | 'assistant'
  text: string
  products?: ChatProduct[]
}

export default function ChatPanel() {
  const navigate = useNavigate()
  const location = useLocation()
  const { shopper, ready } = useAuth()
  const { setMatches } = useMatches()
  const [open, setOpen] = useState(false)
  const [draft, setDraft] = useState('')
  const [sending, setSending] = useState(false)
  const [historyReady, setHistoryReady] = useState(false)
  const [messages, setMessages] = useState<ChatMessage[]>([])
  const [pageName, setPageName] = useState('')
  const logRef = useRef<HTMLDivElement>(null)
  const pageProductId = productIdFromPath(location.pathname)
  const starters = pageProductId
    ? ['Do you have this in navy?', 'What sizes are in stock?']
    : ['What hoodies do you have?', "What's the cheapest hoodie?"]

  useEffect(() => {
    if (!ready) return
    let active = true
    if (!shopper) {
      setMessages([])
      setHistoryReady(true)
      return () => {
        active = false
      }
    }
    setHistoryReady(false)
    fetchChatHistory()
      .then((rows) => {
        if (!active) return
        setMessages(
          rows.map((row) => ({
            id: row.id,
            role: row.role,
            text: row.content,
            products: row.products,
          })),
        )
      })
      .finally(() => {
        if (active) setHistoryReady(true)
      })
    return () => {
      active = false
    }
  }, [ready, shopper])

  useEffect(() => {
    if (!pageProductId) {
      setPageName('')
      return
    }
    let active = true
    fetchProduct(pageProductId)
      .then((product) => {
        if (active) setPageName(product.name)
      })
      .catch(() => {
        if (active) setPageName('')
      })
    return () => {
      active = false
    }
  }, [pageProductId])

  useEffect(() => {
    const log = logRef.current
    if (log) log.scrollTop = log.scrollHeight
  }, [messages, sending, open])

  async function send(text: string) {
    const trimmed = text.trim()
    if (!trimmed || sending || !historyReady) return
    const history = messages.map((message) => ({ role: message.role, content: message.text }))
    const userMessage: ChatMessage = { id: Date.now(), role: 'user', text: trimmed }
    setMessages((current) => [...current, userMessage])
    setDraft('')
    setSending(true)
    try {
      const reply = await sendChatMessage(trimmed, history, pageProductId)
      setMessages((current) => [
        ...current,
        { id: Date.now() + 1, role: 'assistant', text: reply.message, products: reply.products },
      ])
      setMatches(trimmed, reply.products)
      const onlyThisPage = reply.products.length === 1 && reply.products[0].product_id === pageProductId
      if (reply.products.length > 0 && !onlyThisPage) {
        navigate('/products')
      }
    } catch (error) {
      const note = error instanceof Error ? error.message : "The shop assistant couldn't answer."
      setMessages((current) => [...current, { id: Date.now() + 1, role: 'assistant', text: note }])
    } finally {
      setSending(false)
    }
  }

  function onSubmit(event: FormEvent) {
    event.preventDefault()
    void send(draft)
  }

  return (
    <div className="chat-dock">
      {open && (
        <section className="chat-panel" aria-label="Shop chat">
          <header className="chat-header">
            <div>
              <p className="chat-kicker">Campus Customs</p>
              <h2>Ask the shop</h2>
              {pageName && <p className="chat-about">Asking about {pageName}</p>}
            </div>
            <button type="button" className="chat-close" onClick={() => setOpen(false)} aria-label="Close chat">
              ×
            </button>
          </header>
          <div className="chat-log" ref={logRef}>
            {messages.length === 0 && (
              <>
                <p className="chat-empty">
                  Ask about a hoodie, a size, or what's still in stock.
                </p>
                <div className="chat-starters">
                  {starters.map((starter) => (
                    <button
                      key={starter}
                      type="button"
                      className="chat-starter"
                      disabled={sending || !historyReady}
                      onClick={() => void send(starter)}
                    >
                      {starter}
                    </button>
                  ))}
                </div>
              </>
            )}
            {messages.map((message) => (
              <div key={message.id} className={`chat-bubble ${message.role}`}>
                <p>{message.text}</p>
                {message.products && message.products.length > 0 && (
                  <div className="chat-cards">
                    {message.products.map((product) => (
                      <Link key={product.product_id} className="chat-card" to={`/products/${product.product_id}`}>
                        <img src={product.image_url} alt="" />
                        <span>
                          <strong>{product.name}</strong>
                          {formatPrice(product.price)}
                        </span>
                      </Link>
                    ))}
                  </div>
                )}
              </div>
            ))}
            {sending && <p className="chat-bubble assistant pending">Looking that up…</p>}
          </div>
          <form className="chat-form" onSubmit={onSubmit}>
            <input
              value={draft}
              onChange={(event) => setDraft(event.target.value)}
              placeholder="Ask about a piece"
              aria-label="Message"
            />
            <button type="submit" disabled={sending || !historyReady || !draft.trim()}>
              Send
            </button>
          </form>
        </section>
      )}
      <button
        type="button"
        className="chat-launcher"
        aria-expanded={open}
        aria-label={open ? 'Hide shop chat' : 'Open shop chat'}
        onClick={() => setOpen((value) => !value)}
      >
        <svg viewBox="0 0 24 24" aria-hidden="true">
          <path
            d="M5 6.5A2.5 2.5 0 0 1 7.5 4h9A2.5 2.5 0 0 1 19 6.5v7A2.5 2.5 0 0 1 16.5 16H12l-3.6 3.2c-.7.6-1.8.1-1.8-.8V16H7.5A2.5 2.5 0 0 1 5 13.5v-7Z"
            fill="currentColor"
          />
        </svg>
      </button>
    </div>
  )
}
