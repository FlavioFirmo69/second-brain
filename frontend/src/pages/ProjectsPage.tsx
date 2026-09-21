import { useEffect, useState } from 'react'
import { api } from '../api'
import { Panel } from '../components/Panel'
import { Status } from '../components/Status'
import { formatDate } from '../date'
import type { CaseItem, Project } from '../types'

export function ProjectsPage() {
  const [projects, setProjects] = useState<Project[]>([])
  const [cases, setCases] = useState<CaseItem[]>([])
  useEffect(() => { api<Project[]>('/projects').then(setProjects); api<CaseItem[]>('/cases').then(setCases) }, [])
  return <div className="page-grid">
    <Panel title="Progetti"><div className="project-list">{projects.map(p => <details className="project-card" key={p.id}><summary><span><Status value={p.status}/><strong>{p.title}</strong><small>{p.tasks.length} attività · {p.events?.length||0} eventi</small></span><span className="chevron">⌄</span></summary><div className="project-body"><p>{p.objective}</p>{(p.author_name||p.book_title)&&<small>{p.author_name}{p.book_title ? ` · ${p.book_title}` : ''}</small>}<h4>Attività collegate</h4>{p.tasks.length===0?<p className="empty-project">Nessuna attività aperta.</p>:<div className="project-tasks">{p.tasks.map(task=><div key={task.id}><span className="task-dot"/><strong>{task.title}</strong><small>{task.due_date?formatDate(task.due_date):'Senza data'}{task.due_time?` · ${task.due_time.slice(0,5)}`:''}</small></div>)}</div>}<h4>Eventi collegati</h4>{!p.events?.length?<p className="empty-project">Nessun evento futuro.</p>:<div className="project-tasks">{p.events.map(event=><div key={event.id}><span className="event-dot"/><strong>{event.title}</strong><small>{formatDate(event.event_date)}{event.start_time?` · ${event.start_time.slice(0,5)}`:''}</small></div>)}</div>}</div></details>)}</div></Panel>
    <Panel title="Pratiche"><div className="project-list">{cases.map(c => <details className="project-card case-card" key={c.id}><summary><span><Status value={c.status}/><strong>{c.title}</strong><small>{c.tasks?.length||0} attività · {c.events?.length||0} eventi</small></span><span className="chevron">⌄</span></summary><div className="project-body"><p>{c.context_markdown}</p><h4>Attività collegate</h4>{!c.tasks?.length?<p className="empty-project">Nessuna attività aperta.</p>:<div className="project-tasks">{c.tasks.map(task=><div key={task.id}><span className="task-dot"/><strong>{task.title}</strong><small>{task.due_date?formatDate(task.due_date):'Senza data'}{task.due_time?` · ${task.due_time.slice(0,5)}`:''}</small></div>)}</div>}<h4>Eventi collegati</h4>{!c.events?.length?<p className="empty-project">Nessun evento futuro.</p>:<div className="project-tasks">{c.events.map(event=><div key={event.id}><span className="event-dot"/><strong>{event.title}</strong><small>{formatDate(event.event_date)}{event.start_time?` · ${event.start_time.slice(0,5)}`:''}</small></div>)}</div>}</div></details>)}</div></Panel>
  </div>
}
