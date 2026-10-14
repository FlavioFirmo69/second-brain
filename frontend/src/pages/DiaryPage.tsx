import { useEffect, useState } from 'react'
import { api, remove } from '../api'
import { MarkdownView } from '../components/MarkdownView'

type Entry={id:string;conversation_id:string;content_markdown:string;created_at:string;title:string}
type Diary={items:Entry[];total:number;offset:number;limit:number}
const dated=(value:string)=>new Date(value).toLocaleString('it-IT',{timeZone:'Europe/Rome'})

export function DiaryPage() {
  const [search,setSearch]=useState('')
  const [start,setStart]=useState('')
  const [end,setEnd]=useState('')
  const [query,setQuery]=useState({search:'',start:'',end:''})
  const [offset,setOffset]=useState(0)
  const [data,setData]=useState<Diary|null>(null)
  const [busy,setBusy]=useState(false)
  const [error,setError]=useState('')
  const [pendingDelete,setPendingDelete]=useState('')
  const [refresh,setRefresh]=useState(0)
  useEffect(()=>{
    const controller=new AbortController()
    const params=new URLSearchParams({search:query.search,offset:String(offset),limit:'30'})
    if(query.start)params.set('start',query.start)
    if(query.end)params.set('end',query.end)
    setBusy(true);setError('')
    void api<Diary>(`/strategic/diary?${params}`,{signal:controller.signal}).then(result=>{
      if(!controller.signal.aborted)setData(result)
    }).catch(e=>{if(!controller.signal.aborted)setError((e as Error).message)}).finally(()=>{
      if(!controller.signal.aborted)setBusy(false)
    })
    return()=>controller.abort()
  },[query,offset,refresh])
  function open(entry:Entry) {
    window.dispatchEvent(new CustomEvent('second-brain-open-strategic',{detail:{conversationId:entry.conversation_id,text:''}}))
  }
  async function erase(entry:Entry) {
    setBusy(true);setError('')
    try{
      await remove(`/strategic/diary/${entry.id}`)
      setPendingDelete('')
      setData(current=>current?{...current,items:current.items.filter(item=>item.id!==entry.id),total:Math.max(0,current.total-1)}:current)
      if(data?.items.length===1&&offset>0)setOffset(Math.max(0,offset-30))
      else setRefresh(v=>v+1)
    }catch(e){setError((e as Error).message);setBusy(false)}
  }
  return <section className="panel strategic-page">
    <p>Qui trovi i racconti salvati, dai più recenti. Il diario conserva anche i dettagli che il consulente non ha selezionato per la memoria strategica. Le domande di consiglio sono consultabili nelle rispettive conversazioni.</p>
    <button onClick={()=>window.dispatchEvent(new CustomEvent('second-brain-open-strategic',{detail:{conversationId:'',text:''}}))}>Scrivi nel diario o chiedi consiglio</button>
    <button onClick={()=>window.dispatchEvent(new CustomEvent('second-brain-open-strategic',{detail:{conversationId:'',text:'Valuta tutte le attività che sto gestendo rispetto al mio profilo e ai miei desideri. Consigliami dove intervenire, mantenere la rotta o evitare nuovi impegni.'}}))}>Prepara un consiglio sul quadro complessivo</button>
    <form onSubmit={e=>{e.preventDefault();setOffset(0);setQuery({search,start,end})}}>
      <label>Cerca nel diario<input value={search} maxLength={500} onChange={e=>setSearch(e.target.value)} placeholder="HR, AI, Fruit…"/></label>
      <div className="tabs"><label>Dal<input type="date" value={start} onChange={e=>setStart(e.target.value)}/></label><label>Al<input type="date" value={end} onChange={e=>setEnd(e.target.value)}/></label></div>
      <button disabled={busy}>Cerca</button>
    </form>
    {error&&<p role="alert">{error}</p>}
    {busy?<p>Caricamento del diario…</p>:data&&<>
      <p>{data.total} racconti trovati</p>
      {!data.items.length&&<p>Nessun racconto per i filtri selezionati.</p>}
      {data.items.map(entry=><article key={entry.id}>
        <small>{dated(entry.created_at)} · {entry.title}</small>
        <MarkdownView value={entry.content_markdown}/>
        <div className="tabs"><button onClick={()=>open(entry)}>Apri conversazione</button><button disabled={busy} onClick={()=>setPendingDelete(entry.id)}>Elimina episodio</button></div>
        {pendingDelete===entry.id&&<div><p>Eliminare questo racconto dal diario? Gli eventuali ricordi strategici si gestiscono separatamente dalla pagina del consulente.</p><button disabled={busy} onClick={()=>void erase(entry)}>Conferma eliminazione</button><button disabled={busy} onClick={()=>setPendingDelete('')}>Annulla</button></div>}
      </article>)}
      <div className="tabs"><button disabled={offset===0} onClick={()=>setOffset(Math.max(0,offset-30))}>Più recenti</button><button disabled={offset+30>=data.total} onClick={()=>setOffset(offset+30)}>Precedenti</button></div>
    </>}
  </section>
}
