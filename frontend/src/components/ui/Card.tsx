import clsx from 'clsx'
import type { PropsWithChildren } from 'react'

type CardProps = PropsWithChildren<{
  className?: string
}>

export const Card = ({ className, children }: CardProps) => (
  <div
    className={clsx(
      'rounded-xl border border-slate-200 bg-white/70 p-4 shadow-card backdrop-blur-sm',
      className,
    )}
  >
    {children}
  </div>
)

