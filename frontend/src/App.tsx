import { useState } from 'react'
import { CalendarPage } from './pages/CalendarPage'
import { EditorialPage } from './pages/EditorialPage'
import { FinancePage } from './pages/FinancePage'
import { InboxPage } from './pages/InboxPage'
import { ProjectsPage } from './pages/ProjectsPage'
import { SettingsPage } from './pages/SettingsPage'
import { TodayPage } from './pages/TodayPage'
import { AssistantPage } from './pages/AssistantPage'

const pages = [
  ['assistant','Assistente','✦'],['today','Oggi','●'],['calendar','Calendario','□'],['projects','Progetti','◇'],
  ['editorial','Editoria','✦'],['finance','Finanze','€'],['inbox','Inbox','＋'],['settings','Impostazioni','⚙'],
] as const
type Page = typeof pages[number][0]

export default function App() {
  const [page,setPage] = useState<Page>('assistant')
  const content = {assistant:<AssistantPage/>,today:<TodayPage/>,calendar:<CalendarPage/>,projects:<ProjectsPage/>,editorial:<EditorialPage/>,finance:<FinancePage/>,inbox:<InboxPage/>,settings:<SettingsPage/>}[page]
  return <div className="app-shell">
    <aside><div className="brand"><span>2B</span><div><strong>Second Brain</strong><small>Centro operativo</small></div></div><nav>{pages.map(([id,label,icon])=><button className={page===id?'active':''} onClick={()=>setPage(id)} key={id}><span>{icon}</span>{label}</button>)}</nav><footer>Database SQL Server<br/><b>sb2_</b></footer></aside>
    <main><header className="topbar"><div><small>Area personale</small><h1>{pages.find(p=>p[0]===page)?.[1]}</h1></div><span className="online">● Connesso</span></header>{content}</main>
    <nav className="mobile-nav">{pages.map(([id,label,icon])=><button className={page===id?'active':''} onClick={()=>setPage(id)} key={id}><span>{icon}</span><small>{label}</small></button>)}</nav>
  </div>
}
