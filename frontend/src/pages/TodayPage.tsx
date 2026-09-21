import { useEffect, useState } from 'react'
import { api, post } from '../api'
import { Panel } from '../components/Panel'
import type { Dashboard, EventItem, Task } from '../types'

export function TodayPage() {
  const [data, setData] = useState<Dashboard | null>(null)
  const [message, setMessage] = useState('')
  const load = () => api<Dashboard>('/dashboard/today').then(setData).catch(e => setMessage(e.message))
  useEffect(() => { void load() }, [])

  async function complete(task: Task) {
    await post(`/tasks/${task.id}/complete`)
    load()
  }
  async function completeEvent(event: EventItem) {
    await post(`/events/${event.id}/complete`)
    setMessage(`Evento completato: ${event.title}`)
    load()
  }
  return <div className="stack">
    <Panel title="Oggi">
      {message && <p className="notice">{message}</p>}
      {!data ? <p>Caricamento…</p> : <>
        {data.events.length === 0 && data.tasks.filter(t => t.due_date).length === 0 && <p>Nessuna attività pianificata.</p>}
        <div className="list">
          {data.events.map(item => <article key={item.id} className="row"><time>{item.start_time?.slice(0,5) || 'Tutto il giorno'}</time><div><strong>{item.title}</strong>{item.location && <small>{item.location}</small>}</div><button onClick={() => completeEvent(item)}>Fatto</button></article>)}
          {data.tasks.filter(t => t.due_date).map(item => <article key={item.id} className="row"><time>{item.due_time?.slice(0,5) || 'Oggi'}</time><div><strong>{item.title}</strong></div><button onClick={() => complete(item)}>Fatto</button></article>)}
        </div>
      </>}
    </Panel>
    <Panel title="TODO senza data">
      <div className="list compact">{data?.tasks.filter(t => !t.due_date).map(item => <article className="row" key={item.id}><div><strong>{item.title}</strong></div><button onClick={() => complete(item)}>Fatto</button></article>)}</div>
    </Panel>
  </div>
}
