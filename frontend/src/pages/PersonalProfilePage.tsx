import { useEffect, useState } from 'react'
import { api, put } from '../api'
import { MarkdownView } from '../components/MarkdownView'
import type { Profile } from '../types'

type PersonalProfile = {exists:boolean;content_markdown:string;revision:number;updated_at:string|null}

export function PersonalProfilePage() {
  const [profile,setProfile]=useState<PersonalProfile|null>(null)
  const [draft,setDraft]=useState('')
  const [authors,setAuthors]=useState<Profile[]>([])
  const [editing,setEditing]=useState(false)
  const [busy,setBusy]=useState(false)
  const [error,setError]=useState('')
  const [notice,setNotice]=useState('')
  const dirty=!!profile&&draft!==profile.content_markdown
  async function load() {
    setBusy(true);setError('');setNotice('')
    try {
      const result=await api<PersonalProfile>('/personal-profile')
      setProfile(result);setDraft(result.content_markdown);setEditing(!result.exists)
    } catch(e){setError((e as Error).message)} finally{setBusy(false)}
  }
  useEffect(()=>{
    void load()
    void api<Profile[]>('/profiles').then(setAuthors).catch(e=>setError((e as Error).message))
  },[])
  useEffect(()=>{
    const warn=(e:BeforeUnloadEvent)=>{if(dirty){e.preventDefault();e.returnValue=''}}
    window.addEventListener('beforeunload',warn)
    return()=>window.removeEventListener('beforeunload',warn)
  },[dirty])
  async function save(e:React.FormEvent) {
    e.preventDefault();if(!profile||busy)return
    setBusy(true);setError('');setNotice('')
    try {
      const result=await put<PersonalProfile>('/personal-profile',{content_markdown:draft,revision:profile.revision})
      setProfile(result);setDraft(result.content_markdown);setEditing(false)
      setNotice('Profilo salvato. Il consulente userà questa versione dalla prossima risposta.')
    }catch(e){setError((e as Error).message)}finally{setBusy(false)}
  }
  return <section className="panel strategic-page">
    <p>Questo documento descrive la direzione che vuoi dare alla tua vita, i desideri e i confini con cui valutare le scelte. Il consulente lo legge a ogni conversazione.</p>
    <p>Inserisci qui ciò che orienta più ambiti: per esempio il coinvolgimento desiderato nel lavoro dipendente, lo spazio per la scrittura e il tempo personale. Progetti, scadenze e strategie editoriali restano nelle loro pagine.</p>
    {error&&<p role="alert">{error}</p>}
    {notice&&<p className="notice" role="status">{notice}</p>}
    {profile ? <>
      <p>{profile.exists?`Versione ${profile.revision}`:'Profilo ancora da compilare'}{dirty?' · Modifiche non salvate':''}</p>
      <div className="tabs"><button disabled={busy} className={!editing?'active':''} onClick={()=>setEditing(false)}>Leggi documento</button><button disabled={busy} className={editing?'active':''} onClick={()=>setEditing(true)}>Modifica e affina</button></div>
      <form onSubmit={save}>
        {editing?<label>Il tuo profilo<textarea rows={24} style={{minHeight:'420px'}} required maxLength={30000} value={draft} onChange={e=>setDraft(e.target.value)}/></label>:<MarkdownView value={draft}/>}
        {(editing||dirty)&&<button disabled={busy||!draft.trim()}>Salva profilo</button>}
      </form>
      <button disabled={busy} onClick={()=>void load()}>Ricarica la versione salvata</button>
    </>:<p>{busy?'Caricamento…':'Documento non disponibile.'}</p>}
    <h2>Profili autore già presenti</h2>
    <p>Voce, posizionamento e privacy autoriale sono gestiti nei profili esistenti. Il consulente li legge insieme a questo documento.</p>
    {authors.map(author=><details key={author.code}><summary>{author.display_name}</summary><MarkdownView value={[author.positioning,author.voice_markdown,author.privacy_markdown].filter(Boolean).join('\n\n')}/></details>)}
    <button onClick={()=>window.dispatchEvent(new CustomEvent('second-brain-open-settings'))}>Modifica i profili autore</button>
  </section>
}
