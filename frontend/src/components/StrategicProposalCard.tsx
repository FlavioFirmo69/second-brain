import { useState } from 'react'
import { formatDate, isoDateLocal } from '../date'

export type StrategicProposal = {
  id:string; action:string; proposed_date:string; rationale:string;
  status:'proposed'|'accepted'|'rejected'; planned_date?:string; reason?:string;
  strategy_links?:{id:string;title:string;author_name?:string;book_title?:string}[];
}

export function StrategicProposalCard({proposal,busy,onDecide}:{proposal:StrategicProposal;busy:boolean;
  onDecide:(decision:'accepted'|'rejected',planned_date:string,reason:string)=>Promise<void>}) {
  const [planned,setPlanned]=useState(proposal.proposed_date)
  const [rejecting,setRejecting]=useState(false)
  const [reason,setReason]=useState('')
  return <section className="strategic-proposal">
    <strong>{proposal.action}</strong>
    <p>{proposal.rationale}</p>
    {proposal.strategy_links?.map(link=><p key={link.id}><strong>Strategia collegata:</strong> {[link.title,link.author_name,link.book_title].filter(Boolean).join(' · ')}</p>)}
    {proposal.status==='proposed'?<>
      <label>Data proposta (modificabile)<input type="date" min={isoDateLocal()} value={planned} disabled={busy} onChange={e=>setPlanned(e.target.value)}/></label>
      <small>Primo passo da valutare: non è un appuntamento confermato.</small>
      <div className="tabs"><button disabled={busy||!planned||planned<isoDateLocal()} onClick={()=>void onDecide('accepted',planned,'')}>Accetta e registra nel diario</button><button disabled={busy} onClick={()=>setRejecting(true)}>Rifiuta</button></div>
      {rejecting&&<form onSubmit={e=>{e.preventDefault();if(reason.trim())void onDecide('rejected',planned,reason.trim())}}>
        <label>Perché rifiuti questa proposta?<textarea required maxLength={2000} value={reason} disabled={busy} onChange={e=>setReason(e.target.value)} placeholder="Per esempio: preferisco parlarne ad Arona, senza contattarlo prima."/></label>
        <div className="tabs"><button disabled={busy||!reason.trim()}>Registra rifiuto e motivazione</button><button type="button" disabled={busy} onClick={()=>setRejecting(false)}>Annulla</button></div>
      </form>}
    </>:<p role="status">{proposal.status==='accepted'?`Accettata · data prevista ${formatDate(proposal.planned_date||proposal.proposed_date)}. Decisione registrata nel diario.`:`Rifiutata · ${proposal.reason}. Decisione registrata nel diario.`}</p>}
  </section>
}
