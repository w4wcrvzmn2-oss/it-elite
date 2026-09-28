import { cn } from '../../lib/utils'
import type { ButtonHTMLAttributes } from 'react'

interface ButtonProps extends ButtonHTMLAttributes<HTMLButtonElement> {
  variant?: 'primary' | 'secondary' | 'ghost' | 'outline'
  size?: 'sm' | 'md' | 'lg'
}

export function Button({ className, variant = 'primary', size = 'md', ...props }: ButtonProps) {
  const variants = {
    primary: 'bg-leaf text-leaf-ink hover:bg-leaf-glow shadow-glow font-semibold',
    secondary: 'bg-white/[0.04] text-mist-200 border border-white/[0.06] hover:bg-white/[0.08]',
    ghost: 'text-mist-400 hover:bg-white/[0.05] hover:text-mist-50',
    outline: 'border border-white/[0.08] text-mist-200 hover:bg-white/[0.05]',
  }
  const sizes = {
    sm: 'px-3 py-1.5 text-sm',
    md: 'px-4 py-2 text-sm',
    lg: 'px-6 py-3 text-base',
  }
  return (
    <button
      className={cn(
        'inline-flex items-center justify-center gap-2 rounded-xl font-medium transition-colors focus:outline-none focus:ring-2 focus:ring-green-500/30 disabled:opacity-50',
        variants[variant],
        sizes[size],
        className,
      )}
      {...props}
    />
  )
}
