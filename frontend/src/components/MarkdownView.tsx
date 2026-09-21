import type { ElementType, ReactNode } from 'react'

function inline(value: string): ReactNode[] {
  const pattern = /(\*\*[^*]+\*\*|\*[^*]+\*|\[[^\]]+\]\(https?:\/\/[^)]+\))/g
  return value.split(pattern).filter(Boolean).map((part, index) => {
    if (part.startsWith('**')) return <strong key={index}>{part.slice(2,-2)}</strong>
    if (part.startsWith('*')) return <em key={index}>{part.slice(1,-1)}</em>
    const link = part.match(/^\[([^\]]+)\]\((https?:\/\/[^)]+)\)$/)
    if (link) return <a key={index} href={link[2]} target="_blank" rel="noreferrer">{link[1]}</a>
    return part
  })
}

export function MarkdownView({ value }: { value: string }) {
  const blocks = value.replace(/\\n/g, '\n').split(/\n{2,}/).filter(Boolean)
  return <div className="markdown-view">{blocks.map((block, index) => {
    const lines = block.split('\n').map(line => line.trim()).filter(Boolean)
    const heading = lines[0]?.match(/^(#{1,4})\s+(.+)/)
    if (heading && lines.length === 1) {
      const Tag = `h${Math.min(heading[1].length + 2, 5)}` as ElementType
      return <Tag key={index}>{inline(heading[2])}</Tag>
    }
    if (lines.length === 1 && /^-{3,}$/.test(lines[0])) return <hr key={index}/>
    if (lines.every(line => /^>\s?/.test(line))) return <blockquote key={index}>{inline(lines.map(line => line.replace(/^>\s?/, '')).join(' '))}</blockquote>
    if (lines.every(line => /^[-*]\s+/.test(line))) {
      return <ul key={index}>{lines.map((line, i) => <li key={i}>{inline(line.replace(/^[-*]\s+/, ''))}</li>)}</ul>
    }
    if (lines.every(line => /^\d+[.)]\s+/.test(line))) {
      return <ol key={index}>{lines.map((line, i) => <li key={i}>{inline(line.replace(/^\d+[.)]\s+/, ''))}</li>)}</ol>
    }
    return <p key={index}>{lines.map((line, i) => <span key={i}>{inline(line)}{i < lines.length - 1 && <br/>}</span>)}</p>
  })}</div>
}
