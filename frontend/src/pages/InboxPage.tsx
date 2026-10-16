import { useEffect, useState } from 'react'
import { api, patch, post, remove } from '../api'
import { Panel } from '../components/Panel'
import { formatDateTime } from '../date'
import type { InboxItem, Project, CaseItem } from '../types'

type Item=InboxItem&{category:'retry'|'note';details:{last_error?:string;project_id?:string;case_id?:string;conversation_id?:string;result?:unknown}}
type Tab='retry'|'note'|'archive'
export function InboxPage() {
  const [items,setItems]=useState<Item[]>([]),[projects,setProjects]=useState<Project[]>([]),[cases,setCases]=useState<CaseItem[]>([])
  const [tab,setTab]=useState<Tab>('retry'),[search,setSearch]=useState(''),[text,setText]=useState('')
  const [adding,setAdding]=useState(false),[message,setMessage]=useState(''),[working,setWorking]=useState(''),[loading,setLoading]=useState(true)
  const [editing,setEditing]=useState<{id:string;text:string;category:'retry'|'note';context:string}|null>(null)
  const [deleting,setDeleting]=useState('')
  const load=()=>api<Item[]>('/inbox').then(setItems)
  useEffect(()=>{void Promise.all([load(),api<Project[]>('/projects').then(setProjects),api<CaseItem[]>('/cases').then(setCases)]).catch(e=>setMessage((e as Error).message)).finally(()=>setLoading(false))},[])
  async function run(id:string,action:()=>Promise<void>){
    if(working)return
    setWorking(id);setMessage('')
    try{await action();await load()}catch(e){setMessage((e as Error).message)}finally{setWorking('')}
  }
  const archived=(item:Item)=>item.status==='confirmed'
  const matches=(item:Item,filter:Tab)=>filter==='archive'?archived(item):!archived(item)&&item.category===filter
  const visible=items.filter(item=>matches(item,tab)&&item.text.toLocaleLowerCase().includes(search.toLocaleLowerCase()))
  const open=(id:string)=>window.dispatchEvent(new CustomEvent('second-brain-open-chat',{detail:id}))
  const contextLabel=(item:Item)=>projects.find(p=>p.id===item.details.project_id)?.title||cases.find(c=>c.id===item.details.case_id)?.title||'Contesto da definire'
  return <div className="stack inbox-page"><Panel title="Inbox" action={<button disabled={!!working} onClick={()=>setAdding(v=>!v)}>＋ Appunto</button>}>
    <p>Recupera le richieste non riuscite e dai contesto agli appunti ancora da sistemare.</p>
    {message&&<p className="notice" role="status">{message}</p>}
    {adding&&<form className="quick-form" onSubmit={e=>{e.preventDefault();void run('add',async()=>{await post('/inbox',{text:text.trim(),source:'desktop'});setText('');setAdding(false);setTab('note');setMessage('Appunto salvato.')})}}><textarea required rows={3} maxLength={30000} value={text} onChange={e=>setText(e.target.value)} placeholder="Scrivi un appunto, anche senza un contesto…"/><button disabled={!!working||!text.trim()}>Aggiungi</button></form>}
    <div className="tabs">{([['retry','Da riprovare'],['note','Da contestualizzare'],['archive','Archivio']] as const).map(([id,label])=><button key={id} className={tab===id?'active':''} onClick={()=>setTab(id)}>{label} ({items.filter(i=>matches(i,id)).length})</button>)}</div>
    <label className="inbox-search">Cerca<input type="search" value={search} onChange={e=>setSearch(e.target.value)} placeholder="Cerca richieste e appunti"/></label>
    {loading?<p>Caricamento…</p>:!visible.length?<p>Nessun elemento in questa vista.</p>:visible.map(item=><article className="inbox-card" key={item.id}>
      <small>{formatDateTime(item.created_at)} · {archived(item)?item.details.result?'Risolta':'Archiviato':item.status==='interpreted'?'In elaborazione':item.category==='retry'?'Da riprovare':'Appunto'} · {contextLabel(item)}</small>
      <details><summary>{item.text.length>180?item.text.slice(0,180)+'…':item.text}</summary><p className="inbox-full-text">{item.text}</p></details>
      {item.details.last_error&&<p className="inbox-error">Ultimo esito: {item.details.last_error}</p>}
      {item.source==='assistant'&&<small>Elemento precedente dall’assistente: puoi correggere la categoria con Modifica.</small>}
      {editing?.id===item.id&&<form className="inbox-editor" onSubmit={e=>{e.preventDefault();void run(item.id,async()=>{await patch(`/inbox/${item.id}`,{text:editing.text,category:editing.category,project_id:editing.context.startsWith('p:')?editing.context.slice(2):null,case_id:editing.context.startsWith('c:')?editing.context.slice(2):null});setEditing(null);setMessage('Elemento aggiornato.')})}}>
        <label>Testo<textarea required rows={5} maxLength={30000} value={editing.text} onChange={e=>setEditing({...editing,text:e.target.value})}/></label>
        <label>Tipo<select value={editing.category} onChange={e=>setEditing({...editing,category:e.target.value as 'retry'|'note'})}><option value="retry">Richiesta da riprovare</option><option value="note">Appunto da contestualizzare</option></select></label>
        <label>Collega a<select value={editing.context} onChange={e=>setEditing({...editing,context:e.target.value})}><option value="">Nessun contesto</option><optgroup label="Progetti">{projects.map(p=><option key={p.id} value={'p:'+p.id}>{p.title}</option>)}</optgroup><optgroup label="Pratiche">{cases.map(c=><option key={c.id} value={'c:'+c.id}>{c.title}</option>)}</optgroup></select></label>
        <button disabled={!!working||!editing.text.trim()}>Salva modifiche</button><button type="button" onClick={()=>setEditing(null)}>Annulla</button>
      </form>}
      <div className="inbox-actions">
        {item.status==='new'&&<><button disabled={!!working} onClick={()=>setEditing({id:item.id,text:item.text,category:item.category,context:item.details.project_id?'p:'+item.details.project_id:item.details.case_id?'c:'+item.details.case_id:''})}>Modifica e collega</button>
        {item.category==='retry'&&<button className="secondary" disabled={!!working} onClick={()=>void run(item.id,async()=>{const result=await post<{message:string;resolved:boolean;conversation_id?:string}>(`/inbox/${item.id}/retry`);setMessage(result.message);if(result.conversation_id)open(result.conversation_id)})}>{working===item.id?'Elaborazione…':'Riprova richiesta'}</button>}
        <button disabled={!!working} onClick={()=>void run(item.id,async()=>{await post(`/inbox/${item.id}/archive`);setMessage('Elemento archiviato.')})}>Archivia</button></>}
        <button disabled={!!working||item.status==='interpreted'} onClick={()=>void run(item.id,async()=>{const result=await post<{conversation_id:string}>(`/inbox/${item.id}/open`);open(result.conversation_id)})}>{item.details.result?'Apri risultato':item.details.conversation_id?'Apri conversazione':'Apri nell’assistente'}</button>
        <button className="danger" disabled={!!working||item.status==='interpreted'} onClick={()=>setDeleting(item.id)}>Elimina</button>
      </div>
      {item.category==='retry'&&!archived(item)&&<small>Riprova può applicare le operazioni richieste nel testo: controllalo prima di procedere.</small>}
      {deleting===item.id&&<div className="inbox-delete"><p>Eliminare questo elemento dall’Inbox?</p><button disabled={!!working} onClick={()=>void run(item.id,async()=>{await remove(`/inbox/${item.id}`);setDeleting('');setMessage('Elemento eliminato.')})}>Conferma eliminazione</button><button disabled={!!working} onClick={()=>setDeleting('')}>Annulla</button></div>}
    </article>)}
  </Panel></div>
}
