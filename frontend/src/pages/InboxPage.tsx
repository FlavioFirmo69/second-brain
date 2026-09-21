import { useEffect, useState } from 'react'
import { api, post, remove } from '../api'
import { Panel } from '../components/Panel'
import type { InboxItem } from '../types'
import { formatDateTime } from '../date'

export function InboxPage() {
  const [items, setItems] = useState<InboxItem[]>([])
  const [text, setText] = useState('')
  const [message, setMessage] = useState('')
  const [working, setWorking] = useState('')
  const load = () => api<InboxItem[]>('/inbox').then(setItems)
  useEffect(() => { void load() }, [])
  async function add(e: React.FormEvent) { e.preventDefault(); await post('/inbox',{text,source:'desktop'}); setText(''); load() }
  async function discard(item: InboxItem) { setWorking(item.id); try { await remove(`/inbox/${item.id}`); setMessage('Elemento eliminato.'); await load() } finally { setWorking('') } }
  async function execute(item: InboxItem) { setWorking(item.id); setMessage(''); try { const result=await post<{message?:string}>(`/inbox/${item.id}/execute`); setMessage(result.message||'Comando eseguito.'); await load() } catch(e) { setMessage((e as Error).message) } finally { setWorking('') } }
  return <div className="page-grid"><Panel title="Nuova nota"><form className="quick-form" onSubmit={add}><textarea rows={6} value={text} onChange={e=>setText(e.target.value)} placeholder="Cattura una nota senza classificarla…"/><button>Salva nell’inbox</button></form></Panel><Panel title="Da elaborare">{message&&<p className="notice">{message}</p>}<div className="list">{items.map(i=><article className="row inbox-row" key={i.id}><div><strong>{i.text}</strong><small>{formatDateTime(i.created_at)} · {i.status}</small></div><div className="inbox-actions"><button className="secondary" disabled={!i.can_execute||working===i.id} title={i.can_execute?'Esegui comando':'Comando non eseguibile automaticamente'} onClick={()=>void execute(i)}>Esegui</button><button className="danger" disabled={working===i.id} onClick={()=>void discard(i)}>Elimina</button></div></article>)}</div></Panel></div>
}
