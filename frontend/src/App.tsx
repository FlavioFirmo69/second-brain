import { useEffect, useRef, useState } from 'react'
import { WorkDashboard } from './pages/WorkDashboard'
import { PlanningPage } from './pages/PlanningPage'
import { CalendarPage } from './pages/CalendarPage'
import { EditorialPage } from './pages/EditorialPage'
import { FinancePage } from './pages/FinancePage'
import { InboxPage } from './pages/InboxPage'
import { ProjectsPage } from './pages/ProjectsPage'
import { SettingsPage } from './pages/SettingsPage'
import { TodayPage } from './pages/TodayPage'
import { AssistantPage } from './pages/AssistantPage'
import { StrategicPage } from './pages/StrategicPage'
import { PersonalProfilePage } from './pages/PersonalProfilePage'
import { DiaryPage } from './pages/DiaryPage'

const pages = [
  ['strategic','Consulente strategico','◎'],
  ['personal-profile','Profili','◉'],
  ['diary','Diario','▤'],
  ['today','Oggi','●'],['calendar','Calendario','□'],['projects','Progetti','◇'],['dashboard','Dashboard','▦'],['assistant','Assistente','✦'],
  ['planning','Piani e pratiche','▤'],['editorial','Editoria','✦'],['finance','Finanze','€'],['inbox','Inbox','＋'],['settings','Impostazioni','⚙'],
] as const
type Page = typeof pages[number][0]
const strategicPages:Page[]=['strategic','personal-profile','diary']

export default function App() {
  const [page,setPage] = useState<Page>(()=>window.matchMedia('(max-width: 820px)').matches?'today':'dashboard')
  const [moreOpen,setMoreOpen]=useState(false)
  const menuRef=useRef<HTMLDialogElement>(null)
  useEffect(()=>{const dialog=menuRef.current;if(!dialog)return;if(moreOpen&&!dialog.open)dialog.showModal();else if(!moreOpen&&dialog.open)dialog.close()},[moreOpen])
  function navigate(id:Page){setPage(id);setMoreOpen(false)}
  const navigation=()=> <>
    <div className="strategic-nav-group"><button className={page==='strategic'?'active':''} onClick={()=>navigate('strategic')}><span>◎</span>Consulente strategico</button><div className="strategic-subnav">{pages.filter(([id])=>id==='personal-profile'||id==='diary').map(([id,label,icon])=><button key={id} className={page===id?'active':''} onClick={()=>navigate(id)}><span>{icon}</span>{label}</button>)}</div></div>
    {pages.filter(([id])=>!strategicPages.includes(id)).map(([id,label,icon])=><button className={page===id?'active':''} onClick={()=>navigate(id)} key={id}><span>{icon}</span>{label}</button>)}
  </>
  const [context,setContext]=useState('')
  const [chatId,setChatId]=useState('')
  const [strategicRequest,setStrategicRequest]=useState<{conversationId:string;text:string;entryId?:string}|null>(null)
  useEffect(()=>{const diary=()=>setPage('diary');const strategic=(event:Event)=>{setStrategicRequest((event as CustomEvent<{conversationId:string;text:string;entryId?:string}>).detail);setPage('strategic')};window.addEventListener('second-brain-open-diary',diary);window.addEventListener('second-brain-open-strategic',strategic);return()=>{window.removeEventListener('second-brain-open-diary',diary);window.removeEventListener('second-brain-open-strategic',strategic)}},[])
  const [profileVisited,setProfileVisited]=useState(false)
  useEffect(()=>{if(page==='personal-profile')setProfileVisited(true)},[page])
  useEffect(()=>{const open=()=>setPage('personal-profile');const settings=()=>setPage('settings');window.addEventListener('second-brain-open-profile',open);window.addEventListener('second-brain-open-settings',settings);return()=>{window.removeEventListener('second-brain-open-profile',open);window.removeEventListener('second-brain-open-settings',settings)}},[])
  useEffect(()=>{const open=(e:Event)=>{setChatId((e as CustomEvent<string>).detail);setPage('assistant')};window.addEventListener('second-brain-open-chat',open);return()=>window.removeEventListener('second-brain-open-chat',open)},[])
  useEffect(()=>{const open=(event:Event)=>{setContext((event as CustomEvent<string>).detail);setPage('planning')};const projects=()=>setPage('projects');const finance=()=>setPage('finance');window.addEventListener('second-brain-open-finance',finance);window.addEventListener('second-brain-open-projects',projects);window.addEventListener('second-brain-open-context',open);return()=>{window.removeEventListener('second-brain-open-finance',finance);window.removeEventListener('second-brain-open-context',open);window.removeEventListener('second-brain-open-projects',projects)}},[])
  const content = {diary:<DiaryPage/>,'personal-profile':<PersonalProfilePage/>,strategic:<StrategicPage initialRequest={strategicRequest}/>,dashboard:<WorkDashboard/>,planning:<PlanningPage initialContext={context}/>,assistant:<AssistantPage initialConversation={chatId}/>,today:<TodayPage/>,calendar:<CalendarPage/>,projects:<ProjectsPage/>,editorial:<EditorialPage/>,finance:<FinancePage/>,inbox:<InboxPage/>,settings:<SettingsPage/>}[page]
  return <div className="app-shell">
    <aside><div className="brand"><span>2B</span><div><strong>Second Brain</strong><small>Centro operativo</small></div></div><nav>{navigation()}</nav><footer>Database Supabase<br/><b>sb2_</b></footer></aside>
    <main><header className="topbar"><div><small>Area personale</small><h1>{pages.find(p=>p[0]===page)?.[1]}</h1></div><span className="online">● Connesso</span></header>{page!=='personal-profile'&&content}{(profileVisited||page==='personal-profile')&&<div hidden={page!=='personal-profile'}><PersonalProfilePage/></div>}</main>
    <nav className="mobile-nav" aria-label="Navigazione principale">{(['strategic','today','calendar'] as const).map(id=>{const item=pages.find(p=>p[0]===id)!;return <button className={(id==='strategic'?strategicPages.includes(page):page===id)?'active':''} onClick={()=>navigate(id)} key={id}><span>{item[2]}</span><small>{id==='strategic'?'Consulente':item[1]}</small></button>})}<button className={moreOpen||!(['strategic','today','calendar'] as Page[]).includes(page)?'active':''} aria-haspopup="dialog" onClick={()=>setMoreOpen(true)}><span>☰</span><small>Menu</small></button></nav>
    <dialog ref={menuRef} className="mobile-menu" onClose={()=>setMoreOpen(false)} aria-labelledby="mobile-menu-title"><header><h2 id="mobile-menu-title">Menu</h2><button onClick={()=>setMoreOpen(false)} aria-label="Chiudi menu">✕</button></header><nav>{navigation()}</nav></dialog>
  </div>
}
