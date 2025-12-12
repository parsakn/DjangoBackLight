import { forwardRef } from 'react'
import type { InputHTMLAttributes } from 'react'
import clsx from 'clsx'

type InputProps = InputHTMLAttributes<HTMLInputElement> & {
  label?: string
  error?: string
}

export const Input = forwardRef<HTMLInputElement, InputProps>(
  ({ label, error, className, ...rest }, ref) => {
    return (
      <label className="flex flex-col gap-1 text-sm text-slate-700">
        {label && <span className="font-medium text-slate-800">{label}</span>}
        <input
          ref={ref}
          className={clsx(
            'w-full rounded-lg border border-slate-200 bg-white px-3 py-2 text-sm text-slate-900 shadow-sm outline-none transition focus:border-slate-400 focus:ring-2 focus:ring-slate-200',
            error && 'border-rose-300 focus:ring-rose-100',
            className,
          )}
          {...rest}
        />
        {error && <span className="text-xs text-rose-600">{error}</span>}
      </label>
    )
  },
)

Input.displayName = 'Input'

