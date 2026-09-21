import { useEffect, useState } from 'react'
import { api, put } from '../api'
import { Panel } from '../components/Panel'
import { MarkdownView } from '../components/MarkdownView'
import type { Profile } from '../types'

export function SettingsPage() {
  const [profiles, setProfiles] = useState<Profile[]>([])
  const [selected, setSelected] = useState<Profile | null>(null)
  const [message, setMessage] = useState('')
  const [rules, setRules] = useState('')
  const load = () => api<Profile[]>('/profiles').then(items => { setProfiles(items); setSelected(current => current ? items.find(x=>x.code===current.code) || items[0] : items[0]) })
  useEffect(() => { void load(); void api<{content_markdown:string}>('/manuals/deterministic-rules').then(data=>setRules(data.content_markdown)) }, [])
  async function save(e: React.FormEvent) { e.preventDefault(); if(!selected) return; await put(`/profiles/${selected.code}`,{positioning:selected.positioning,voice_markdown:selected.voice_markdown,privacy_markdown:selected.privacy_markdown,change_reason:'Modifica da interfaccia'}); setMessage('Nuova versione attivata.'); load() }
  return <div className="stack"><Panel title="Profili autoriali">
    <div className="tabs">{profiles.map(p=><button className={selected?.code===p.code?'active':''} key={p.code} onClick={()=>setSelected(p)}>{p.display_name}</button>)}</div>
    {selected && <form className="editor" onSubmit={save}>{message&&<p className="notice">{message}</p>}<label>Posizionamento<textarea rows={3} value={selected.positioning} onChange={e=>setSelected({...selected,positioning:e.target.value})}/></label><label>Voce (Markdown)<textarea rows={12} value={selected.voice_markdown} onChange={e=>setSelected({...selected,voice_markdown:e.target.value})}/></label><label>Privacy (Markdown)<textarea rows={5} value={selected.privacy_markdown} onChange={e=>setSelected({...selected,privacy_markdown:e.target.value})}/></label><button>Salva nuova versione</button></form>}
  </Panel><Panel title="Regole deterministiche"><p className="read-only-note">Promemoria in sola lettura · applicate direttamente dal backend</p>{rules ? <MarkdownView value={rules}/> : <p>Caricamento…</p>}</Panel></div>
}
