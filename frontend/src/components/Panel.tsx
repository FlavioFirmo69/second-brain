import type { ReactNode } from 'react'

export function Panel({ title, action, children }: { title: string; action?: ReactNode; children: ReactNode }) {
  return <section className="panel"><header><h2>{title}</h2>{action}</header>{children}</section>
}

