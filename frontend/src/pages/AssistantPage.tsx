import { useEffect, useRef, useState } from 'react'
import { api, post } from '../api'
import { MarkdownView } from '../components/MarkdownView'
import { formatDate } from '../date'
import type { ChatMessage, ChatResponse, Conversation, Dashboard, EventItem, Finance, Task } from '../types'

type StructuredResult={kind:string;message?:string;data?:Record<string,unknown>}

function messageResult(message:ChatMessage):StructuredResult|null {
  const value=message.metadata?.result
  return value&&typeof value==='object' ? value as StructuredResult : null
}

export function AssistantPage() {
  const [conversations,setConversations] = useState<Conversation[]>([])
  const [active,setActive] = useState('')
  const [messages,setMessages] = useState<ChatMessage[]>([])
  const [text,setText] = useState('')
  const [busy,setBusy] = useState(false)
  const [error,setError] = useState('')
  const [copied,setCopied] = useState('')
  const bottom = useRef<HTMLDivElement>(null)

  useEffect(() => { void loadConversations() }, [])
  useEffect(() => { bottom.current?.scrollIntoView({behavior:'smooth'}) }, [messages,busy])

  async function loadConversations() {
    try {
      const items = await api<Conversation[]>('/conversations')
      setConversations(items)
      if (items[0]) await choose(items[0].id)
    } catch (e) { setError((e as Error).message) }
  }
  async function choose(id:string) {
    setActive(id); setError('')
    setMessages(await api<ChatMessage[]>(`/conversations/${id}/messages`))
  }
  async function createConversation() {
    const item = await post<Conversation>('/conversations',{title:'Nuova conversazione'})
    setConversations(current=>[item,...current]); setActive(item.id); setMessages([]); setText('')
    return item.id
  }
  async function send(e:React.FormEvent) {
    e.preventDefault(); const prompt=text.trim(); if (!prompt || busy) return
    setBusy(true); setError(''); setText('')
    try {
      const id=active || await createConversation()
      const optimistic:ChatMessage={id:`local-${Date.now()}`,role:'user',content_markdown:prompt,message_kind:'text',created_at:new Date().toISOString()}
      setMessages(current=>[...current,optimistic])
      const response=await post<ChatResponse>(`/conversations/${id}/messages`,{text:prompt})
      setMessages(current=>[...current.filter(item=>item.id!==optimistic.id),response.user_message,response.assistant_message])
      setConversations(await api<Conversation[]>('/conversations'))
    } catch (e) { setError((e as Error).message) } finally { setBusy(false) }
  }
  async function copyArticle(message:ChatMessage) {
    const node=document.getElementById(`article-content-${message.id}`); if (!node) return
    const html=node.innerHTML; const plain=node.innerText
    if (navigator.clipboard && 'ClipboardItem' in window) {
      await navigator.clipboard.write([new ClipboardItem({'text/html':new Blob([html],{type:'text/html'}),'text/plain':new Blob([plain],{type:'text/plain'})})])
    } else await navigator.clipboard.writeText(plain)
    setCopied(message.id); window.setTimeout(()=>setCopied(''),1800)
  }
  async function completeCalendarItem(messageId:string,kind:'event'|'task',itemId:string) {
    await post(`/${kind==='event'?'events':'tasks'}/${itemId}/complete`)
    setMessages(current=>current.map(message=>{
      if(message.id!==messageId)return message
      const result=messageResult(message); if(!result?.data)return message
      const key=kind==='event'?'events':'tasks'
      const list=Array.isArray(result.data[key]) ? result.data[key] as Array<{id:string}> : []
      return {...message,metadata:{...message.metadata,result:{...result,data:{...result.data,[key]:list.filter(item=>item.id!==itemId)}}}}
    }))
  }
  function structured(message:ChatMessage) {
    const result=messageResult(message); if(!result)return null
    if(result.kind==='dashboard') {
      const data=result.data as unknown as Dashboard
      const planned=data.tasks?.filter(item=>item.due_date)||[], todos=data.tasks?.filter(item=>!item.due_date)||[]
      return <div className="assistant-result"><header><span>Oggi</span><strong>{formatDate(data.date)}</strong></header><div className="assistant-agenda">
        {data.events?.map(item=><AgendaRow key={item.id} time={(item.start_time?.slice(0,5)||'Tutto il giorno')+(item.end_time?`–${item.end_time.slice(0,5)}`:'')} title={item.title} detail={item.location} onDone={()=>void completeCalendarItem(message.id,'event',item.id)}/>)}
        {planned.map(item=><AgendaRow key={item.id} time={item.due_time?.slice(0,5)||'Oggi'} title={item.title} onDone={()=>void completeCalendarItem(message.id,'task',item.id)}/>)}
        {!data.events?.length&&!planned.length&&<p className="empty-result">Nessun impegno pianificato per oggi.</p>}
      </div>{todos.length>0&&<section className="assistant-todos"><h4>TODO senza data</h4>{todos.map(item=><AgendaRow key={item.id} time="TODO" title={item.title} onDone={()=>void completeCalendarItem(message.id,'task',item.id)}/>)}</section>}</div>
    }
    if(result.kind==='week') {
      const data=result.data as {start:string;end:string;tasks:Task[];events:EventItem[]}
      return <div className="assistant-result"><header><span>Settimana</span><strong>{formatDate(data.start)} – {formatDate(data.end)}</strong></header><div className="assistant-agenda">{data.events?.map(item=><AgendaRow key={item.id} time={`${formatDate(item.event_date)} · ${item.start_time?.slice(0,5)||'—'}${item.end_time?`–${item.end_time.slice(0,5)}`:''}`} title={item.title} onDone={()=>void completeCalendarItem(message.id,'event',item.id)}/>)}{data.tasks?.map(item=><AgendaRow key={item.id} time={item.due_date?formatDate(item.due_date):'TODO'} title={item.title} onDone={()=>void completeCalendarItem(message.id,'task',item.id)}/>)}</div></div>
    }
    if(result.kind==='finance') {
      const data=result.data as unknown as Finance
      return <div className="assistant-result"><header><span>Saldo</span><strong>{data.balance?`${Number(data.balance.balance).toLocaleString('it-IT',{style:'currency',currency:'EUR'})}`:'Non disponibile'}</strong></header><div className="assistant-agenda">{data.planned?.map(item=><AgendaRow key={item.id} time={formatDate(item.transaction_date)} title={item.description} detail={Number(item.amount).toLocaleString('it-IT',{style:'currency',currency:'EUR'})}/>)}</div></div>
    }
    return null
  }
  function keyDown(e:React.KeyboardEvent<HTMLTextAreaElement>) { if (e.key==='Enter'&&!e.shiftKey) { e.preventDefault(); e.currentTarget.form?.requestSubmit() } }

  return <div className="assistant-shell">
    <section className="conversation-list">
      <button className="new-chat" onClick={()=>void createConversation()}>＋ Nuova conversazione</button>
      <div>{conversations.map(item=><button key={item.id} className={active===item.id?'active':''} onClick={()=>void choose(item.id)}>{item.title}</button>)}</div>
    </section>
    <section className="chat-panel">
      <div className="chat-scroll">
        {messages.length===0&&<div className="chat-welcome"><span>✦</span><h2>Come posso aiutarti?</h2><p>Organizziamo attività, sviluppiamo strategie o scriviamo un articolo nella voce di uno dei tuoi autori.</p></div>}
        {messages.map(message=><article key={message.id} className={`chat-message ${message.role}`}>
          {message.message_kind==='article' ? <div className="article-draft">
            <div id={`article-content-${message.id}`}><header><small>{String(message.metadata?.author_code||'Bozza editoriale')}</small><h2>{String(message.metadata?.title||'Articolo')}</h2>{Boolean(message.metadata?.subtitle)&&<p>{String(message.metadata?.subtitle)}</p>}</header><MarkdownView value={message.content_markdown}/></div>
            <button className="copy-article" onClick={()=>void copyArticle(message)}>{copied===message.id?'Copiato ✓':'Copia per Substack'}</button>
          </div> : structured(message)||<MarkdownView value={message.content_markdown}/>} 
        </article>)}
        {busy&&<div className="thinking">Sto elaborando…</div>}
        {error&&<p className="notice error">{error}</p>}<div ref={bottom}/>
      </div>
      <form className="chat-composer" onSubmit={send}><textarea rows={2} value={text} onChange={e=>setText(e.target.value)} onKeyDown={keyDown} placeholder="Scrivi al tuo Second Brain…"/><button disabled={busy||!text.trim()}>Invia</button><small>Invio per spedire · Maiusc+Invio per andare a capo</small></form>
    </section>
  </div>
}

function AgendaRow({time,title,detail,onDone}:{time:string;title:string;detail?:string;onDone?:()=>void}) {
  return <div className="assistant-agenda-row"><time>{time}</time><div><strong>{title}</strong>{detail&&<small>{detail}</small>}</div>{onDone&&<button onClick={onDone} title="Segna come fatto" aria-label={`Segna come fatto ${title}`}><svg viewBox="0 0 24 24"><path d="m5 12 4 4L19 6"/></svg></button>}</div>
}
