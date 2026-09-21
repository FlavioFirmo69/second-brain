import { useEffect, useState } from 'react'
import { api, post } from '../api'
import { Panel } from '../components/Panel'
import type { Finance } from '../types'
import { formatDate, isoDateLocal } from '../date'

const eur = new Intl.NumberFormat('it-IT', { style: 'currency', currency: 'EUR' })
export function FinancePage() {
  const [data, setData] = useState<Finance | null>(null)
  const [balance, setBalance] = useState('')
  const load = () => api<Finance>('/finance').then(setData)
  useEffect(() => { void load() }, [])
  async function update(e: React.FormEvent) {
    e.preventDefault()
    await post('/finance/balance', { account_code:'ING_CURRENT', balance:Number(balance), balance_date:isoDateLocal() })
    setBalance(''); load()
  }
  return <div className="page-grid">
    <Panel title="Saldo"><div className="balance">{data?.balance ? eur.format(data.balance.balance) : '—'}</div><small>Aggiornato al {formatDate(data?.balance?.balance_date)}</small><form className="inline-form" onSubmit={update}><input type="number" step="0.01" value={balance} onChange={e => setBalance(e.target.value)} placeholder="Nuovo saldo"/><button>Aggiorna</button></form></Panel>
    <Panel title="Movimenti previsti"><div className="list">{data?.planned.map(m => <article className="row" key={m.id}><time>{formatDate(m.transaction_date)}</time><div><strong>{m.description}</strong><small>Saldo previsto {eur.format(m.projected_balance)}</small></div><b className={m.amount < 0 ? 'negative' : 'positive'}>{eur.format(m.amount)}</b></article>)}</div></Panel>
  </div>
}
