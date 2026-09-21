import { useEffect, useState } from 'react'
import { api, post } from '../api'
import { MarkdownView } from '../components/MarkdownView'
import { Panel } from '../components/Panel'
import { Status } from '../components/Status'
import { formatDate, isoDateLocal } from '../date'
import type { SaleProgress, Strategy } from '../types'

export function EditorialPage() {
  const [strategies, setStrategies] = useState<Strategy[]>([])
  const [sales, setSales] = useState<SaleProgress>({items:[]})
  const [book, setBook] = useState('')
  const [quantity, setQuantity] = useState('')
  const [saleDate, setSaleDate] = useState(isoDateLocal())
  const [channel, setChannel] = useState('')
  const [message, setMessage] = useState('')
  const load = () => Promise.all([api<Strategy[]>('/strategies').then(setStrategies), api<SaleProgress>('/sales').then(data => { setSales(data); setBook(current => current || data.items[0]?.code || '') })])
  useEffect(() => { void load() }, [])

  async function addSale(e: React.FormEvent) {
    e.preventDefault()
    const amount = Number(quantity)
    if (!book || !Number.isInteger(amount) || amount <= 0) { setMessage('Inserisci un numero di copie valido.'); return }
    await post('/sales', { book_code:book, quantity:amount, sale_date:saleDate, channel:channel || null, notes:null })
    const title = sales.items.find(item => item.code === book)?.title || book
    setMessage(`Registrate ${amount} copie di ${title}.`)
    setQuantity(''); setChannel(''); await load()
  }

  return <div className="stack">
    <Panel title="Vendite e target">
      <div className="cards">{sales.items.map(item => <article className="metric" key={item.code}><h3>{item.title}</h3><strong>{item.sold} / {item.target_value ?? '—'}</strong><small>Scadenza {formatDate(item.target_date)}</small><Status value={item.status}/></article>)}</div>
      <form className="sale-form" onSubmit={addSale}>
        <h3>Registra nuove vendite</h3>
        {message && <p className="notice">{message}</p>}
        <label>Libro<select value={book} onChange={e=>setBook(e.target.value)}>{sales.items.map(item=><option value={item.code} key={item.code}>{item.title}</option>)}</select></label>
        <label>Copie vendute<input required min="1" step="1" type="number" value={quantity} onChange={e=>setQuantity(e.target.value)}/></label>
        <label>Data vendita<input required type="date" value={saleDate} onChange={e=>setSaleDate(e.target.value)}/></label>
        <label>Canale (facoltativo)<input value={channel} onChange={e=>setChannel(e.target.value)} placeholder="Es. Amazon, evento, diretto"/></label>
        <button>Registra vendita</button>
      </form>
    </Panel>
    <Panel title="Strategie attive"><div className="strategy-list">{strategies.map(s => <details className="strategy-card" key={s.id} open><summary><span><strong>{s.title}</strong>{s.book_title&&<small>{s.book_title}</small>}</span><span className="lock-mark" title="Sola lettura" aria-label="Sola lettura">▣</span></summary><MarkdownView value={s.content_markdown}/></details>)}</div></Panel>
  </div>
}
