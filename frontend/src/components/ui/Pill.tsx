import clsx from 'clsx'
import type { PropsWithChildren } from 'react'

type PillProps = PropsWithChildren<{
  tone?: 'slate' | 'green' | 'orange' | 'blue' | 'rose'
  className?: string
}>

const tones = {
  slate: 'bg-slate-100 text-slate-700',
  green: 'bg-emerald-100 text-emerald-700',
  orange: 'bg-amber-100 text-amber-700',
  blue: 'bg-sky-100 text-sky-700',
  rose: 'bg-rose-100 text-rose-700',
}

export const Pill = ({ children, tone = 'slate', className }: PillProps) => (
  <span
    className={clsx(
      'inline-flex items-center gap-1 rounded-full px-2.5 py-1 text-xs font-semibold',
      tones[tone],
      className,
    )}
  >
    {children}
  </span>
)

