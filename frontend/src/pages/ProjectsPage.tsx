import { useEffect, useState } from 'react'
import { api, post, remove } from '../api'
import { Panel } from '../components/Panel'
import { Status } from '../components/Status'
import { formatDate } from '../date'
import type { CaseItem, Profile, Project, Task } from '../types'

export function ProjectsPage() {
  const [projects, setProjects] = useState<Project[]>([])
  const [cases, setCases] = useState<CaseItem[]>([])
  const [profiles,setProfiles]=useState<Profile[]>([])
  const [completedTasks,setCompletedTasks]=useState<Task[]>([])
  const [pendingDelete,setPendingDelete]=useState<Task|null>(null)
  const [deleting,setDeleting]=useState(false)
  const [incorrectInformation,setIncorrectInformation]=useState(false)
  const [deleteReason,setDeleteReason]=useState('')
  function requestDelete(task:Task){setIncorrectInformation(false);setDeleteReason('');setPendingDelete(task)}
  async function deleteActivity(task:Task){
    setDeleting(true);setMessage('')
    try{
      await remove(`/tasks/${task.id}?incorrect_information=${incorrectInformation}&reason=${encodeURIComponent(deleteReason)}`)
      setCompletedTasks(items=>items.filter(t=>t.id!==task.id))
      setProjects(items=>items.map(p=>({...p,tasks:p.tasks.filter(t=>t.id!==task.id)})))
      setCases(items=>items.map(c=>({...c,tasks:c.tasks?.filter(t=>t.id!==task.id)})))
      setPendingDelete(null);setMessage(`Attività eliminata: ${task.title}`)
    }catch(e){setMessage((e as Error).message)}finally{setDeleting(false)}
  }
  const taskControls=(task:Task)=><span>{pendingDelete?.id===task.id?<><span>Eliminare questa attività?</span><label><input type="checkbox" checked={incorrectInformation} disabled={deleting} onChange={e=>setIncorrectInformation(e.target.checked)}/> Informazione non vera: correggi la valutazione del consulente</label><input aria-label="Motivo della correzione" maxLength={1000} disabled={deleting} value={deleteReason} onChange={e=>setDeleteReason(e.target.value)} placeholder="Ad esempio: il libro non è stato pubblicato"/><button disabled={deleting} onClick={()=>void deleteActivity(task)}>Conferma eliminazione</button><button disabled={deleting} onClick={()=>setPendingDelete(null)}>Annulla</button></>:<button disabled={deleting} onClick={()=>requestDelete(task)}>Elimina</button>}</span>
  const pastSection=(items:Task[])=><details><summary>Attività scadute già completate ({items.length})</summary>{items.length?<div className="project-tasks">{items.map(task=><div key={task.id}><strong>{task.title}</strong><small>{task.due_date?formatDate(task.due_date):''} · Completata</small>{taskControls(task)}</div>)}</div>:<p>Nessuna attività completata con data precedente a oggi.</p>}</details>
  const [showForm,setShowForm]=useState(false),[kind,setKind]=useState<'project'|'book'>('project')
  const [code,setCode]=useState(''),[title,setTitle]=useState(''),[objective,setObjective]=useState(''),[authorCode,setAuthorCode]=useState(''),[publicationDate,setPublicationDate]=useState(''),[message,setMessage]=useState('')
  const load=()=>Promise.all([api<Project[]>('/projects').then(setProjects),api<CaseItem[]>('/cases').then(setCases),api<Task[]>('/tasks/completed-past').then(setCompletedTasks)])
  useEffect(() => { void load().catch(e=>setMessage((e as Error).message));void api<Profile[]>('/profiles').then(setProfiles).catch(e=>setMessage((e as Error).message)) }, [])
  async function createProject(e:React.FormEvent){e.preventDefault();setMessage('');await post('/projects',{kind,code,title,objective:objective||null,author_code:authorCode||null,publication_date:kind==='book'&&publicationDate?publicationDate:null});setMessage(kind==='book'?'Libro e progetto creati.':'Progetto creato.');setCode('');setTitle('');setObjective('');setPublicationDate('');setShowForm(false);await load()}
  return <div className="page-grid">
    <Panel title="Progetti" action={<button className="primary" onClick={()=>setShowForm(value=>!value)}>＋ Nuovo</button>}>
      {message&&<p className="notice">{message}</p>}
      {showForm&&<form className="project-create-form" onSubmit={createProject}><label>Tipo<select value={kind} onChange={e=>setKind(e.target.value as 'project'|'book')}><option value="project">Progetto generale</option><option value="book">Nuovo libro</option></select></label><label>Codice<input required pattern="[A-Za-z0-9_-]+" value={code} onChange={e=>setCode(e.target.value.toUpperCase())} placeholder="NUOVO_LIBRO"/></label><label>Titolo<input required value={title} onChange={e=>setTitle(e.target.value)}/></label><label>Autore<select required={kind==='book'} value={authorCode} onChange={e=>setAuthorCode(e.target.value)}><option value="">Nessun autore</option>{profiles.map(profile=><option key={profile.id} value={profile.code}>{profile.display_name}</option>)}</select></label>{kind==='book'&&<label>Pubblicazione prevista<input type="date" value={publicationDate} onChange={e=>setPublicationDate(e.target.value)}/></label>}<label className="wide">Obiettivo<textarea rows={2} value={objective} onChange={e=>setObjective(e.target.value)} placeholder="Risultato che vuoi ottenere"/></label><div className="form-buttons wide"><button type="button" onClick={()=>setShowForm(false)}>Annulla</button><button className="primary">Crea</button></div></form>}
      <div className="project-list">{projects.map(p => <details className="project-card" key={p.id}><summary><span><Status value={p.status}/><strong>{p.title}</strong><small>{p.tasks.length} attività · {p.events?.length||0} eventi</small></span><span className="chevron">⌄</span></summary><div className="project-body">{p.book_id&&<button onClick={()=>window.dispatchEvent(new CustomEvent('second-brain-open-context',{detail:'book:'+p.book_id}))}>Apri libro e strategia</button>}<p>{p.objective}</p>{(p.author_name||p.book_title)&&<small>{p.author_name}{p.book_title ? ` · ${p.book_title}` : ''}</small>}<h4>Attività collegate</h4>{p.tasks.length===0?<p className="empty-project">Nessuna attività aperta.</p>:<div className="project-tasks">{p.tasks.map(task=><div key={task.id}><span className="task-dot"/><strong>{task.title}</strong><small>{task.due_date?formatDate(task.due_date):'Senza data'}{task.due_time?` · ${task.due_time.slice(0,5)}`:''}</small>{taskControls(task)}</div>)}</div>}{pastSection(completedTasks.filter(t=>t.project_id===p.id||(!t.project_id&&!!p.book_id&&t.book_id===p.book_id)))}<h4>Eventi collegati</h4>{!p.events?.length?<p className="empty-project">Nessun evento futuro.</p>:<div className="project-tasks">{p.events.map(event=><div key={event.id}><span className="event-dot"/><strong>{event.title}</strong><small>{formatDate(event.event_date)}{event.start_time?` · ${event.start_time.slice(0,5)}`:''}</small></div>)}</div>}</div></details>)}</div>
    </Panel>
    <Panel title="Pratiche"><div className="project-list">{cases.map(c => <details className="project-card case-card" key={c.id}><summary><span><Status value={c.status}/><strong>{c.title}</strong><small>{c.tasks?.length||0} attività · {c.events?.length||0} eventi</small></span><span className="chevron">⌄</span></summary><div className="project-body"><button onClick={()=>window.dispatchEvent(new CustomEvent('second-brain-open-context',{detail:'case:'+c.id}))}>Apri pratica</button><p>{c.context_markdown}</p><h4>Attività collegate</h4>{!c.tasks?.length?<p className="empty-project">Nessuna attività aperta.</p>:<div className="project-tasks">{c.tasks.map(task=><div key={task.id}><span className="task-dot"/><strong>{task.title}</strong><small>{task.due_date?formatDate(task.due_date):'Senza data'}{task.due_time?` · ${task.due_time.slice(0,5)}`:''}</small>{taskControls(task)}</div>)}</div>}{pastSection(completedTasks.filter(t=>t.case_id===c.id))}<h4>Eventi collegati</h4>{!c.events?.length?<p className="empty-project">Nessun evento futuro.</p>:<div className="project-tasks">{c.events.map(event=><div key={event.id}><span className="event-dot"/><strong>{event.title}</strong><small>{formatDate(event.event_date)}{event.start_time?` · ${event.start_time.slice(0,5)}`:''}</small></div>)}</div>}</div></details>)}</div></Panel>
  </div>
}
