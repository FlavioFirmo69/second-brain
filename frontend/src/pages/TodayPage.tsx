import { useEffect, useMemo, useState } from 'react'
import { api, patch, post } from '../api'
import { Panel } from '../components/Panel'
import { formatDate } from '../date'
import type { Dashboard, EventItem, Task } from '../types'

type WeekData={start:string;end:string;tasks:Task[];events:EventItem[]}
type AgendaItem={id:string;kind:'event'|'task';date?:string;time?:string;title:string;detail?:string;source:EventItem|Task}

function asItems(events:EventItem[],tasks:Task[]):AgendaItem[]{
  return [...events.map(item=>({id:item.id,kind:'event' as const,date:item.event_date,time:item.start_time?.slice(0,5),title:item.title,detail:item.location,source:item})),...tasks.map(item=>({id:item.id,kind:'task' as const,date:item.due_date,time:item.due_time?.slice(0,5),title:item.title,detail:item.project_title||item.case_title,source:item}))].sort((a,b)=>(a.date||'9999').localeCompare(b.date||'9999')||(a.time||'99:99').localeCompare(b.time||'99:99')||a.title.localeCompare(b.title))
}

export function TodayPage() {
  const [data, setData] = useState<Dashboard | null>(null)
  const [week,setWeek]=useState<WeekData|null>(null)
  const [message, setMessage] = useState('')
  const load=()=>Promise.all([api<Dashboard>('/dashboard/today'),api<WeekData>('/dashboard/week')]).then(([day,weekData])=>{setData(day);setWeek(weekData)}).catch(e=>setMessage(e.message))
  useEffect(() => { void load() }, [])

  const todayItems=useMemo(()=>data?asItems(data.events,data.tasks.filter(item=>Boolean(item.due_date))):[],[data])
  const laterItems=useMemo(()=>data&&week?asItems(week.events.filter(item=>item.event_date>data.date),week.tasks.filter(item=>Boolean(item.due_date)&&item.due_date!>data.date)):[],[data,week])
  const todos=useMemo(()=>week?.tasks.filter(item=>!item.due_date)||data?.tasks.filter(item=>!item.due_date)||[],[data,week])
  const laterDays=[...new Set(laterItems.map(item=>item.date).filter(Boolean))] as string[]

  async function complete(item:AgendaItem){await post(`/${item.kind==='event'?'events':'tasks'}/${item.id}/complete`);setMessage(`Completato: ${item.title}`);await load()}
  async function schedule(task:Task,event:React.FormEvent<HTMLFormElement>){
    event.preventDefault()
    const form=new FormData(event.currentTarget)
    const dueDate=String(form.get('due_date')||'')
    if(!dueDate)return
    try{
      await patch(`/tasks/${task.id}/schedule`,{due_date:dueDate,due_time:null})
      setMessage(`Pianificato per il ${formatDate(dueDate)}: ${task.title}`)
      await load()
    }catch(error){setMessage(error instanceof Error?error.message:'Impossibile pianificare l’attività')}
  }
  const row=(item:AgendaItem)=><article key={`${item.kind}-${item.id}`} className="row today-row"><time>{item.time||'—'}</time><div><strong>{item.title}</strong>{item.detail&&<small>{item.detail}</small>}</div><button className="done-icon" onClick={()=>void complete(item)} title="Segna come fatto" aria-label={`Segna come fatto ${item.title}`}>✓</button></article>
  const todoRow=(item:Task)=><article key={item.id} className="row today-row todo-row"><div className="todo-description"><strong>{item.title}</strong>{(item.project_title||item.case_title)&&<small>{item.project_title||item.case_title}</small>}</div><form className="todo-schedule" onSubmit={event=>void schedule(item,event)}><input type="date" name="due_date" required aria-label={`Data per ${item.title}`}/><button type="submit" title="Assegna data" aria-label={`Assegna data a ${item.title}`}>📅</button></form><button className="done-icon" onClick={()=>void complete({id:item.id,kind:'task',title:item.title,source:item})} title="Segna come fatto" aria-label={`Segna come fatto ${item.title}`}>✓</button></article>

  return <div className="stack today-page">
    <Panel title="Oggi">
      {message && <p className="notice">{message}</p>}
      {!data?<p>Caricamento…</p>:<div className="list compact">{todayItems.length?todayItems.map(row):<p className="empty-state compact-empty">Nessuna attività pianificata.</p>}</div>}
    </Panel>
    <Panel title="Resto della settimana">
      {!week?<p>Caricamento…</p>:laterDays.length?<div className="week-sections">{laterDays.map(day=><section key={day}><h3>{new Date(`${day}T12:00:00`).toLocaleDateString('it-IT',{weekday:'long',day:'2-digit',month:'2-digit'})}</h3><div className="list compact">{laterItems.filter(item=>item.date===day).map(row)}</div></section>)}</div>:<p className="empty-state compact-empty">Nessun altro impegno questa settimana.</p>}
    </Panel>
    <Panel title="TODO">
      <div className="list compact">{todos.length?todos.map(todoRow):<p className="empty-state compact-empty">Nessun TODO aperto.</p>}</div>
    </Panel>
  </div>
}
