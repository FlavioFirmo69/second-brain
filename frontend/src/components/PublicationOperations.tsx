import { useEffect, useState } from 'react'
import { api, post, remove } from '../api'
import { formatDate, isoDateLocal } from '../date'
import type { Book, SaleProgress } from '../types'

export type Inventory={items:Array<{code:string;title:string;purchased:number;sold:number;available:number}>;purchases:Array<{id:string;book_code:string;title:string;purchase_date:string;quantity:number}>}

export function PublicationOperations({book,stock,purchases,sales,onSaved}:{book:Book;stock?:Inventory['items'][number];purchases:Inventory['purchases'];sales:NonNullable<SaleProgress['recent_sales']>;onSaved:()=>Promise<unknown>}) {
  const [mode,setMode]=useState<'sale'|'purchase'|null>(null)
  const [quantity,setQuantity]=useState(''),[day,setDay]=useState(isoDateLocal())
  const [format,setFormat]=useState<'ebook'|'paperback'>('ebook'),[fromStock,setFromStock]=useState(false),[channel,setChannel]=useState('')
  const [busy,setBusy]=useState(false),[message,setMessage]=useState('')
  const [historyOpen,setHistoryOpen]=useState(false),[historyLoading,setHistoryLoading]=useState(false),[recentSales,setRecentSales]=useState(sales)
  useEffect(()=>{
    if(!historyOpen){setRecentSales(sales);return}
    let active=true;setHistoryLoading(true)
    void api<SaleProgress>(`/sales?book_code=${encodeURIComponent(book.code)}`).then(data=>{if(active)setRecentSales(data.recent_sales||[])}).catch(e=>{if(active)setMessage((e as Error).message)}).finally(()=>{if(active)setHistoryLoading(false)})
    return()=>{active=false}
  },[historyOpen,book.code,sales])
  async function save(e:React.FormEvent){
    e.preventDefault();const amount=Number(quantity)
    if(!Number.isInteger(amount)||amount<1){setMessage('Inserisci un numero intero positivo di copie.');return}
    setBusy(true);setMessage('')
    try{
      if(mode==='purchase')await post('/planning/inventory',{book_code:book.code,quantity:amount,purchase_date:day})
      else await post('/sales',{book_code:book.code,quantity:amount,sale_date:day,format_code:format,from_inventory:format==='paperback'&&fromStock,channel:channel||null,notes:null})
      setMessage(mode==='purchase'?'Copie caricate in magazzino.':'Vendita registrata.')
      setQuantity('');setChannel('');setMode(null);await onSaved()
    }catch(e){setMessage((e as Error).message)}finally{setBusy(false)}
  }
  async function discard(path:string,label:string){
    if(!window.confirm(`Eliminare ${label} di «${book.title}»?`))return
    setBusy(true);setMessage('')
    try{await remove(path);await onSaved();setMessage('Registrazione eliminata.')}catch(e){setMessage((e as Error).message)}finally{setBusy(false)}
  }
  return <section className="publication-operations">
    <h3>Vendite e copie cartacee</h3>
    <p>Magazzino: <strong>{stock?.available??0} copie disponibili</strong> · Acquistate {stock?.purchased??0} · Vendute dal magazzino {stock?.sold??0}</p>
    {message&&<p className="notice" role="status">{message}</p>}
    <div className="form-buttons"><button disabled={busy} onClick={()=>{setMode('sale');setQuantity('');setMessage('')}}>Registra vendita</button><button disabled={busy} onClick={()=>{setMode('purchase');setQuantity('');setMessage('')}}>Carica copie cartacee</button></div>
    {mode&&<form className="sale-form publication-form" onSubmit={save}>
      <h4>{mode==='purchase'?'Acquisto copie autore da Amazon':'Nuova vendita'} · {book.title}</h4>
      {mode==='sale'&&<><label>Formato<select value={format} onChange={e=>setFormat(e.target.value as 'ebook'|'paperback')}><option value="ebook">Ebook</option><option value="paperback">Cartaceo</option></select></label>{format==='paperback'&&<label>Provenienza<select value={fromStock?'stock':'external'} onChange={e=>setFromStock(e.target.value==='stock')}><option value="external">Vendita esterna (es. Amazon)</option><option value="stock">Dal mio magazzino</option></select></label>}</>}
      <label>{mode==='purchase'?'Copie acquistate':'Copie vendute'}<input required type="number" min="1" step="1" value={quantity} onChange={e=>setQuantity(e.target.value)}/></label>
      <label>Data<input required type="date" value={day} onChange={e=>setDay(e.target.value)}/></label>
      {mode==='sale'&&<label>Canale facoltativo<input value={channel} onChange={e=>setChannel(e.target.value)} placeholder="Amazon, evento, diretto…"/></label>}
      <div className="form-buttons"><button type="button" disabled={busy} onClick={()=>setMode(null)}>Annulla</button><button disabled={busy}>Salva</button></div>
    </form>}
    <details onToggle={e=>setHistoryOpen(e.currentTarget.open)}><summary>Storico vendite · ultime 50 del libro</summary>{historyLoading?<p>Caricamento vendite…</p>:recentSales.length?recentSales.map(s=><div className="sale-row" key={s.id}><time>{formatDate(s.sale_date)}</time><span>{s.quantity} copie · {s.format_code==='ebook'?'Ebook':s.format_code==='paperback'?'Cartaceo':'Formato non indicato'}</span><small>{s.from_inventory?'Dal magazzino · ':''}{s.channel||'Canale non indicato'}</small><button disabled={busy} onClick={()=>void discard(`/sales/${s.id}`,'questa vendita')}>Elimina vendita</button></div>):<p>Nessuna vendita presente nello storico recente.</p>}</details>
    <details><summary>Acquisti copie cartacee ({purchases.length})</summary>{purchases.length?purchases.map(p=><div className="sale-row" key={p.id}><time>{formatDate(p.purchase_date)}</time><span>+{p.quantity} copie · Amazon</span><button disabled={busy} onClick={()=>void discard(`/planning/inventory/${p.id}`,'questo acquisto')}>Elimina acquisto</button></div>):<p>Nessun acquisto registrato.</p>}</details>
  </section>
}
