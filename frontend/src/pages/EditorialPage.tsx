import { useEffect, useState } from 'react'
import { api, post, put } from '../api'
import { MarkdownView } from '../components/MarkdownView'
import { Panel } from '../components/Panel'
import { Status } from '../components/Status'
import { formatDate, isoDateLocal } from '../date'
import type { Book, Profile, SaleProgress, Strategy } from '../types'

export function EditorialPage() {
  const [strategies, setStrategies] = useState<Strategy[]>([])
  const [books,setBooks]=useState<Book[]>([])
  const [profiles,setProfiles]=useState<Profile[]>([])
  const [sales, setSales] = useState<SaleProgress>({items:[]})
  const [book, setBook] = useState('')
  const [quantity, setQuantity] = useState('')
  const [saleDate, setSaleDate] = useState(isoDateLocal())
  const [channel, setChannel] = useState('')
  const [message, setMessage] = useState('')
  const load = () => Promise.all([api<Strategy[]>('/strategies').then(setStrategies),api<Book[]>('/books').then(setBooks),api<Profile[]>('/profiles').then(setProfiles), api<SaleProgress>('/sales').then(data => { setSales(data); setBook(current => current || data.items[0]?.code || '') })])
  useEffect(() => { void load() }, [])

  async function addSale(e: React.FormEvent) {
    e.preventDefault()
    const amount = Number(quantity)
    if (!book || !Number.isInteger(amount) || amount <= 0) { setMessage('Inserisci un numero di copie valido.'); return }
    await post('/sales', { book_code:book, quantity:amount, sale_date:saleDate, channel:channel || null, notes:null })
    const title = sales.items.find(item => item.code === book)?.title || book
    setMessage(`Registrate ${amount} copie di ${title}.`)
    setQuantity(''); setChannel(''); await load()
  }

  return <div className="stack">
    <Panel title="Schede libri"><div className="book-list">{books.map(item=><BookCard key={item.id} book={item} profiles={profiles} onSaved={load}/>)}</div></Panel>
    <Panel title="Vendite e target">
      <div className="cards">{sales.items.map(item => <article className="metric" key={item.code}><h3>{item.title}</h3><strong>{item.sold} / {item.target_value ?? '—'}</strong><small>Scadenza {formatDate(item.target_date)}</small><Status value={item.status}/></article>)}</div>
      <form className="sale-form" onSubmit={addSale}>
        <h3>Registra nuove vendite</h3>
        {message && <p className="notice">{message}</p>}
        <label>Libro<select value={book} onChange={e=>setBook(e.target.value)}>{sales.items.map(item=><option value={item.code} key={item.code}>{item.title}</option>)}</select></label>
        <label>Copie vendute<input required min="1" step="1" type="number" value={quantity} onChange={e=>setQuantity(e.target.value)}/></label>
        <label>Data vendita<input required type="date" value={saleDate} onChange={e=>setSaleDate(e.target.value)}/></label>
        <label>Canale (facoltativo)<input value={channel} onChange={e=>setChannel(e.target.value)} placeholder="Es. Amazon, evento, diretto"/></label>
        <button>Registra vendita</button>
      </form>
    </Panel>
    <Panel title="Strategie attive"><div className="strategy-list">{strategies.map(s => <details className="strategy-card" key={s.id} open><summary><span><strong>{s.title}</strong>{s.book_title&&<small>{s.book_title}</small>}</span><span className="lock-mark" title="Sola lettura" aria-label="Sola lettura">▣</span></summary><MarkdownView value={s.content_markdown}/></details>)}</div></Panel>
  </div>
}

function BookCard({book,profiles,onSaved}:{book:Book;profiles:Profile[];onSaved:()=>Promise<unknown>}){
  const [editing,setEditing]=useState(false),[title,setTitle]=useState(book.title),[authorCode,setAuthorCode]=useState(book.author_code),[status,setStatus]=useState(book.status),[publicationDate,setPublicationDate]=useState(book.publication_date||''),[formatNotes,setFormatNotes]=useState(book.format_notes||''),[genre,setGenre]=useState(book.genre||''),[synopsis,setSynopsis]=useState(book.synopsis||''),[themes,setThemes]=useState(book.themes||''),[targetReader,setTargetReader]=useState(book.target_reader||''),[positioning,setPositioning]=useState(book.positioning||''),[differentiators,setDifferentiators]=useState(book.differentiators||''),[toneNotes,setToneNotes]=useState(book.tone_notes||''),[message,setMessage]=useState('')
  async function save(e:React.FormEvent){e.preventDefault();setMessage('');await put(`/books/${book.id}`,{title,author_code:authorCode,status,publication_date:publicationDate||null,format_notes:formatNotes||null,genre:genre||null,synopsis:synopsis||null,themes:themes||null,target_reader:targetReader||null,positioning:positioning||null,differentiators:differentiators||null,tone_notes:toneNotes||null});setMessage('Scheda aggiornata.');setEditing(false);await onSaved()}
  return <details className="book-card"><summary><span><Status value={book.status}/><span><strong>{book.title}</strong><small>{book.author_name} · {book.code}</small></span></span><span className="chevron">⌄</span></summary><div className="book-body">
    {!editing?<><div className="book-facts"><div><small>Autore</small><strong>{book.author_name}</strong></div><div><small>Stato editoriale</small><strong>{book.status}</strong></div><div><small>Genere</small><strong>{book.genre||'—'}</strong></div><div><small>Pubblicazione</small><strong>{formatDate(book.publication_date)}</strong></div><div><small>Vendite</small><strong>{book.sold}{book.target_value!=null?` / ${book.target_value}`:''}</strong></div><div><small>Formato / note</small><strong>{book.format_notes||'—'}</strong></div></div><div className="book-context"><section><h4>Sinossi</h4><p>{book.synopsis||'Non compilata.'}</p></section><section><h4>Temi</h4><p>{book.themes||'Non compilati.'}</p></section><section><h4>Lettore ideale</h4><p>{book.target_reader||'Non compilato.'}</p></section><section><h4>Posizionamento</h4><p>{book.positioning||'Non compilato.'}</p></section><section><h4>Elementi distintivi</h4><p>{book.differentiators||'Non compilati.'}</p></section><section><h4>Tono del libro</h4><p>{book.tone_notes||'Non compilato.'}</p></section></div><div className="book-links"><section><h4>Progetti collegati</h4>{book.projects.length?book.projects.map(project=><div key={project.id}><strong>{project.title}</strong><small>{project.objective||project.code}</small></div>):<p>Nessun progetto collegato.</p>}</section><section><h4>Strategie collegate</h4>{book.strategies.length?book.strategies.map(strategy=><div key={strategy.id}><strong>{strategy.title}</strong><small>Versione {strategy.version_number}</small></div>):<p>Nessuna strategia collegata.</p>}</section></div><button className="secondary-action" onClick={()=>setEditing(true)}>Modifica anagrafica</button></>:<form className="book-edit-form" onSubmit={save}><label>Titolo<input required value={title} onChange={e=>setTitle(e.target.value)}/></label><label>Autore<select required value={authorCode} onChange={e=>setAuthorCode(e.target.value)}>{profiles.map(profile=><option key={profile.id} value={profile.code}>{profile.display_name}</option>)}</select></label><label>Stato editoriale<select value={status} onChange={e=>setStatus(e.target.value)}><option value="writing">In scrittura</option><option value="draft">Bozza completa</option><option value="ready">Pronto</option><option value="publishing">In pubblicazione</option><option value="promotion">In promozione</option><option value="published">Pubblicato</option><option value="archived">Archiviato</option></select></label><label>Data pubblicazione<input type="date" value={publicationDate} onChange={e=>setPublicationDate(e.target.value)}/></label><label>Genere<input maxLength={120} value={genre} onChange={e=>setGenre(e.target.value)} placeholder="Romanzo, saggio…"/></label><label>Formato / note<input maxLength={500} value={formatNotes} onChange={e=>setFormatNotes(e.target.value)}/></label><label className="wide">Sinossi<textarea rows={5} value={synopsis} onChange={e=>setSynopsis(e.target.value)}/></label><label className="wide">Temi principali<textarea rows={3} value={themes} onChange={e=>setThemes(e.target.value)} placeholder="Separati da virgole o descritti liberamente"/></label><label className="wide">Lettore ideale<textarea rows={3} value={targetReader} onChange={e=>setTargetReader(e.target.value)}/></label><label className="wide">Posizionamento editoriale<textarea rows={3} value={positioning} onChange={e=>setPositioning(e.target.value)}/></label><label className="wide">Promessa ed elementi distintivi<textarea rows={3} value={differentiators} onChange={e=>setDifferentiators(e.target.value)}/></label><label className="wide">Tono e indicazioni di voce<textarea rows={3} value={toneNotes} onChange={e=>setToneNotes(e.target.value)}/></label><div className="form-buttons wide"><button type="button" onClick={()=>setEditing(false)}>Annulla</button><button className="primary">Salva</button></div></form>}
    {message&&<p className="notice">{message}</p>}
  </div></details>
}
