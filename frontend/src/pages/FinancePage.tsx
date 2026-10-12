import { useEffect, useState } from 'react'
import { api, post } from '../api'
import { Panel } from '../components/Panel'
import type { Finance } from '../types'
import { formatDate, isoDateLocal } from '../date'

const eur = new Intl.NumberFormat('it-IT', { style: 'currency', currency: 'EUR' })
export function FinancePage() {
  const [data, setData] = useState<Finance | null>(null)
  const [balance, setBalance] = useState('')
  const [movementDate,setMovementDate]=useState(isoDateLocal())
  const [description,setDescription]=useState('')
  const [amount,setAmount]=useState('')
  const [movementType,setMovementType]=useState<'expense'|'income'>('expense')
  const [message,setMessage]=useState('')
  const [completing,setCompleting]=useState<string | null>(null)
  const [completionMessage,setCompletionMessage]=useState('')
  const load = () => api<Finance>('/finance').then(setData)
  useEffect(() => { void load() }, [])
  async function update(e: React.FormEvent) {
    e.preventDefault()
    await post('/finance/balance', { account_code:'ING_CURRENT', balance:Number(balance), balance_date:isoDateLocal() })
    setBalance(''); load()
  }
  async function addMovement(e:React.FormEvent){
    e.preventDefault();setMessage('')
    const value=Math.abs(Number(amount))*(movementType==='expense'?-1:1)
    await post('/finance/transactions',{account_code:'ING_CURRENT',transaction_date:movementDate,description:description.trim(),amount:value})
    setDescription('');setAmount('');setMessage('Movimento previsionale aggiunto.');await load()
  }
  async function completeMovement(id:string, amount:number){
    if(completing) return
    setCompleting(id);setCompletionMessage('')
    try {
      await post(`/finance/transactions/${id}/confirm`)
      setData(current=>current ? {...current,planned:current.planned.filter(m=>m.id!==id)} : current)
      setCompletionMessage(amount<0 ? 'Pagamento segnato come eseguito.' : 'Incasso segnato come eseguito.')
      try { await load() } catch { setCompletionMessage('Movimento eseguito. Ricarica la pagina per aggiornare i saldi previsti.') }
    } catch(error) {
      setCompletionMessage(error instanceof Error ? error.message : 'Impossibile aggiornare il movimento.')
    } finally { setCompleting(null) }
  }
  return <div className="page-grid">
    <Panel title="Saldo"><div className="balance">{data?.balance ? eur.format(data.balance.balance) : '—'}</div><small>Aggiornato al {formatDate(data?.balance?.balance_date)}</small><form className="inline-form" onSubmit={update}><input type="number" step="0.01" value={balance} onChange={e => setBalance(e.target.value)} placeholder="Nuovo saldo"/><button>Aggiorna</button></form></Panel>
    <Panel title="Nuovo movimento previsto"><form className="movement-form" onSubmit={addMovement}><label>Data<input required type="date" value={movementDate} onChange={e=>setMovementDate(e.target.value)}/></label><label>Descrizione<input required maxLength={500} value={description} onChange={e=>setDescription(e.target.value)} placeholder="Pagamento Cogeme"/></label><label>Tipo<select value={movementType} onChange={e=>setMovementType(e.target.value as 'expense'|'income')}><option value="expense">Uscita</option><option value="income">Entrata</option></select></label><label>Importo €<input required type="number" min="0.01" step="0.01" value={amount} onChange={e=>setAmount(e.target.value)} placeholder="50,00"/></label><button className="primary">Aggiungi</button></form>{message&&<p className="notice">{message}</p>}</Panel>
    <Panel title="Movimenti previsti"><p className="notice">Segna i pagamenti e gli incassi eseguiti per rimuoverli dalle previsioni. Aggiorna il saldo effettivo nel riquadro Saldo.</p>{completionMessage&&<p role="status" className="notice">{completionMessage}</p>}<div className="list">{data?.planned.length?data.planned.map(m => <article className="row finance-row" key={m.id}><time>{formatDate(m.transaction_date)}</time><div><strong>{m.description}</strong><small>Saldo previsto {eur.format(m.projected_balance)}</small></div><b className={m.amount < 0 ? 'negative' : 'positive'}>{eur.format(m.amount)}</b><button type="button" disabled={completing!==null} onClick={()=>void completeMovement(m.id,m.amount)}>{completing===m.id ? 'Salvataggio…' : m.amount<0 ? 'Segna pagato' : 'Segna incassato'}</button></article>):<p className="empty-state compact-empty">Nessun movimento pianificato.</p>}</div></Panel>
  </div>
}
