import { useState } from 'react'
import { useForm } from 'react-hook-form'
import { z } from 'zod'
import { zodResolver } from '@hookform/resolvers/zod'
import { useNavigate, Link } from 'react-router-dom'
import { Button } from '../../components/ui/Button'
import { Input } from '../../components/ui/Input'
import { useAuth } from '../../auth/AuthProvider'
import { getApiErrorMessage } from '../../api/http'

const schema = z.object({
  username: z.string().min(1, 'Username is required'),
  password: z.string().min(1, 'Password is required'),
})

type FormValues = z.infer<typeof schema>

export const LoginPage = () => {
  const { login } = useAuth()
  const navigate = useNavigate()
  const [serverError, setServerError] = useState<string | null>(null)
  const {
    register,
    handleSubmit,
    formState: { errors, isSubmitting },
  } = useForm<FormValues>({
    resolver: zodResolver(schema),
    defaultValues: { username: '', password: '' },
  })

  const onSubmit = async (values: FormValues) => {
    setServerError(null)
    try {
      await login(values)
      navigate('/', { replace: true })
    } catch (error) {
      const message = getApiErrorMessage(
        error,
        'Login failed. Please check your credentials and try again.',
      )
      setServerError(message)
    }
  }

  return (
    <div className="flex min-h-screen items-center justify-center bg-gradient-to-br from-slate-50 via-white to-slate-100 p-4">
      <div className="w-full max-w-md rounded-2xl border border-slate-200 bg-white/80 p-8 shadow-card backdrop-blur">
        <div className="mb-6 text-center">
          <p className="text-xs uppercase tracking-[0.2em] text-slate-500">SmartLight</p>
          <h1 className="text-2xl font-semibold text-slate-900">Welcome back</h1>
          <p className="text-sm text-slate-600">Sign in to manage your homes and lamps.</p>
        </div>
        <form onSubmit={handleSubmit(onSubmit)} className="space-y-4">
          <Input label="Username" placeholder="your.username" {...register('username')} error={errors.username?.message} />
          <Input
            label="Password"
            type="password"
            placeholder="••••••••"
            {...register('password')}
            error={errors.password?.message}
          />
          {serverError && <div className="rounded-lg bg-rose-50 px-3 py-2 text-sm text-rose-700">{serverError}</div>}
          <Button type="submit" className="w-full" loading={isSubmitting}>
            Sign in
          </Button>
        </form>
        <p className="mt-6 text-center text-sm text-slate-600">
          No account?{' '}
          <Link to="/register" className="font-semibold text-slate-900 underline">
            Create one
          </Link>
        </p>
      </div>
    </div>
  )
}

