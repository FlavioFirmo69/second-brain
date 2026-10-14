import { useEffect, useState } from 'react'
import { api, post, remove } from '../api'
import { MarkdownView } from '../components/MarkdownView'

type Memory = {id:string;kind:string;content:string;rationale:string;source_refs:string[]}
type Conversation = {id:string;title:string}
type Message = {role:string;content_markdown:string;message_kind:string}

export function StrategicPage({initialRequest=null}:{initialRequest?:{conversationId:string;text:string;entryId?:string}|null}) {
  const [chats,setChats]=useState<Conversation[]>([])
  const [id,setId]=useState('')
  const [messages,setMessages]=useState<Message[]>([])
  const [text,setText]=useState('')
  const [busy,setBusy]=useState(false)
  const [error,setError]=useState('')
  const [memories,setMemories]=useState<Memory[]>([])
  const [entryId,setEntryId]=useState<string|undefined>(undefined)
  async function load() {
    setChats(await api<Conversation[]>('/strategic/conversations'))
    setMemories(await api<Memory[]>('/strategic/memories'))
  }
  useEffect(()=>{void load().catch(e=>setError(String(e)))},[])
  useEffect(()=>{
    if(initialRequest){setText(initialRequest.text);void choose(initialRequest.conversationId).then(()=>setEntryId(initialRequest.entryId)).catch(e=>setError(String(e)))}
  },[initialRequest])
  async function choose(cid:string) {
    setEntryId(undefined)
    setId(cid)
    setMessages(cid?await api<Message[]>(`/conversations/${cid}/messages`):[])
  }
  async function send(mode:'diary'|'advice') {
    if(busy||(mode==='diary'&&!text.trim()))return
    setBusy(true);setError('')
    const prompt=text.trim()||(mode==='advice'?'Valuta nel complesso le attività che sto gestendo rispetto al mio profilo, ai miei desideri e ai miei vincoli. Dove dovrei intervenire, mantenere la rotta o evitare nuovi impegni?':'')
    try {
      const result=await post<{conversation_id:string;message:string}>('/strategic/advice',{text:prompt,conversation_id:id||null,mode,diary_entry_id:entryId||null})
      setId(result.conversation_id)
      setMessages(current=>[...current,{role:'user',content_markdown:prompt,message_kind:mode==='diary'?'strategic_diary':'strategic_question'},{role:'assistant',content_markdown:result.message,message_kind:'strategic_advice'}])
      setText('');setEntryId(undefined);await load()
    } catch(e){setError(String(e))} finally{setBusy(false)}
  }
  return <section className="panel strategic-page">
    <p>Il consulente valuta le attività che stai gestendo rispetto al tuo profilo, ai tuoi desideri e ai tuoi vincoli: lavoro, consulenze, scrittura e tempo personale. Il diario arricchisce il quadro complessivo.</p>
    <button disabled={busy} onClick={()=>void send('advice')}>Consiglio sulle attività che sto gestendo</button>
    <button onClick={()=>window.dispatchEvent(new CustomEvent('second-brain-open-profile'))}>Leggi e affina il tuo profilo e i tuoi desideri</button>
    <button disabled={busy} onClick={()=>window.dispatchEvent(new CustomEvent('second-brain-open-diary'))}>Consulta il diario</button>
    {error&&<p role="alert">{error}</p>}
    <label>Conversazione <select disabled={busy} value={id} onChange={e=>void choose(e.target.value).catch(e=>setError(String(e)))}><option value="">Nuova riflessione</option>{chats.map(c=><option key={c.id} value={c.id}>{c.title}</option>)}</select></label>
    {messages.map((m,i)=><article key={i}><strong>{m.role==='user'?'Tu':'Consulente strategico'}</strong><MarkdownView value={m.content_markdown}/></article>)}
    <form onSubmit={e=>{e.preventDefault();void send('diary')}}><label>Diario o domanda al consulente<textarea required maxLength={12000} placeholder="Racconta un fatto oppure chiedi come orientare gli impegni rispetto alle tue priorità." value={text} onChange={e=>setText(e.target.value)}/></label><div className="tabs"><button disabled={busy||!text.trim()}>Registra nel diario</button><button type="button" disabled={busy} onClick={()=>void send('advice')}>Chiedi consiglio sul quadro complessivo</button></div><small>Il consiglio confronta tutte le attività con il profilo, anche senza scrivere una domanda. Registrare un racconto attiva la memoria selettiva; chiedere consiglio non rielabora automaticamente il diario per creare ricordi.</small></form>
    <h2>Memoria trasversale</h2><p>Questi ricordi sono stati selezionati dal consulente. Il racconto completo resta nella conversazione; i dettagli occasionali non diventano memoria permanente. Il consulente non crea attività né modifica i progetti.</p>
    {memories.map(m=><article key={m.id}><MarkdownView value={m.content}/><small>{m.rationale}</small><button disabled={busy} onClick={()=>{setBusy(true);void remove(`/strategic/memories/${m.id}`).then(load).catch(e=>setError(String(e))).finally(()=>setBusy(false))}}>Dimentica</button></article>)}
  </section>
}
