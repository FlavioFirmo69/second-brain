import { useState } from 'react'
import { patch } from '../api'
import { formatDate, isoDateLocal } from '../date'
import { Panel } from './Panel'
import type { Book } from '../types'

export function PublicationTimeline({books,onSaved}:{books:Book[];onSaved:()=>Promise<unknown>}){
  const [start,setStart]=useState(isoDateLocal().slice(0,7)),[author,setAuthor]=useState('all')
  const [selected,setSelected]=useState(''),[target,setTarget]=useState(''),[note,setNote]=useState('')
  const [busy,setBusy]=useState(false),[message,setMessage]=useState('')
  const authors=[...new Map(books.map(b=>[b.author_code,b.author_name])).entries()]
  const visible=books.filter(b=>author==='all'||b.author_code===author)
  const planned=visible.filter(b=>b.planned_release_date).sort((a,b)=>a.planned_release_date!.localeCompare(b.planned_release_date!))
  const months=Array.from({length:12},(_,i)=>{const [y,m]=start.split('-').map(Number);return new Date(y,m-1+i,1,12)})
  const key=(d:Date)=>isoDateLocal(d).slice(0,7)
  const outside=planned.filter(b=>!months.some(m=>key(m)===b.planned_release_date!.slice(0,7)))
  function choose(id:string){const b=books.find(b=>b.id===id);setSelected(id);setTarget(b?.planned_release_date||'');setNote(b?.release_plan_note||'');setMessage('')}
  async function save(e:React.FormEvent){e.preventDefault();if(!selected||busy)return;setBusy(true);setMessage('');try{
    await patch(`/books/${selected}/release-target`,{planned_release_date:target||null,release_plan_note:note||null});await onSaved();setMessage(target?'Data obiettivo salvata.':'Data obiettivo rimossa.')
  }catch(e){setMessage((e as Error).message)}finally{setBusy(false)}}
  return <Panel title="Timeline delle pubblicazioni">
    <p>Date obiettivo indipendenti, distinte dalla pubblicazione effettiva. Ogni data può essere modificata senza spostare gli altri titoli.</p>
    <div className="publication-filters"><label>Profilo<select value={author} onChange={e=>setAuthor(e.target.value)}><option value="all">Tutti i profili</option>{authors.map(([code,name])=><option key={code} value={code}>{name}</option>)}</select></label><label>Periodo dal mese<input type="month" required value={start} onChange={e=>{if(e.target.value)setStart(e.target.value)}}/></label></div>
    {!planned.length&&<p>Nessuna uscita prevista per questo profilo. Imposta una data obiettivo nel modulo sotto.</p>}
    <div className="release-timeline" role="region" aria-label="Timeline grafica delle uscite previste" tabIndex={0}>
      <div className="release-grid">
        <div className="release-author">Profilo</div>{months.map(m=><div className="release-month" key={key(m)}>{m.toLocaleDateString('it-IT',{month:'short',year:'numeric'})}</div>)}
        {authors.filter(([code])=>author==='all'||code===author).map(([code,name],index)=><div className="release-lane" key={code} style={{'--release-color':index%2?'#9d6420':'#315e9e'} as React.CSSProperties}>
          <div className="release-author">{name}</div>{months.map(m=><div className="release-cell" key={key(m)}>{planned.filter(b=>b.author_code===code&&b.planned_release_date!.slice(0,7)===key(m)).map(b=><button className="release-milestone" key={b.id} title={b.release_plan_note||'Modifica la data obiettivo'} onClick={()=>choose(b.id)}><span aria-hidden="true">◆</span><strong>{b.title}</strong><small>Obiettivo {formatDate(b.planned_release_date)}</small></button>)}</div>)}
        </div>)}
      </div>
    </div>
    <details className="release-chronology"><summary>Elenco cronologico delle uscite previste ({planned.length})</summary>{planned.map(b=><p key={b.id}><strong>{formatDate(b.planned_release_date)}</strong> · {b.author_name} · {b.title} <button onClick={()=>choose(b.id)}>Modifica</button></p>)}</details>
    {!!outside.length&&<p>{outside.length} uscite sono fuori dal periodo visualizzato: sono consultabili nell’elenco cronologico.</p>}
    <form className="book-edit-form" onSubmit={save}><label>Pubblicazione<select required value={selected} onChange={e=>choose(e.target.value)}><option value="">Scegli un titolo</option>{visible.map(b=><option key={b.id} value={b.id}>{b.author_name} · {b.title}</option>)}</select></label><label>Data obiettivo di uscita<input type="date" value={target} onChange={e=>setTarget(e.target.value)}/></label><label className="wide">Note e flessibilità<textarea maxLength={1000} rows={2} value={note} onChange={e=>setNote(e.target.value)} placeholder="Per esempio: entro fine novembre; data indicativa"/></label><button disabled={busy||!selected}>Salva previsione</button></form>
    <small>Per pianificare un titolo nuovo, crealo prima in Progetti → Nuovo libro. Lascia vuota la data per rimuovere una previsione.</small>
    {message&&<p className="notice" role="status">{message}</p>}
  </Panel>
}
