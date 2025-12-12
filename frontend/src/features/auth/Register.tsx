import { useState } from 'react'
import { useForm } from 'react-hook-form'
import { z } from 'zod'
import { zodResolver } from '@hookform/resolvers/zod'
import { useNavigate, Link } from 'react-router-dom'
import { Button } from '../../components/ui/Button'
import { Input } from '../../components/ui/Input'
import { useAuth } from '../../auth/AuthProvider'

const schema = z
  .object({
    username: z.string().min(1, 'Username is required'),
    email: z.string().email('Enter a valid email'),
    phone_number: z.string().min(5, 'Phone is required'),
    password: z.string().min(6, 'At least 6 characters'),
    password2: z.string().min(6, 'Please confirm your password'),
  })
  .refine((values) => values.password === values.password2, {
    message: 'Passwords must match',
    path: ['password2'],
  })

type FormValues = z.infer<typeof schema>

export const RegisterPage = () => {
  const { register: registerUser } = useAuth()
  const navigate = useNavigate()
  const [serverError, setServerError] = useState<string | null>(null)
  const {
    register,
    handleSubmit,
    formState: { errors, isSubmitting },
  } = useForm<FormValues>({
    resolver: zodResolver(schema),
    defaultValues: {
      username: '',
      email: '',
      phone_number: '',
      password: '',
      password2: '',
    },
  })

  const onSubmit = async (values: FormValues) => {
    setServerError(null)
    try {
      await registerUser(values)
      navigate('/', { replace: true })
    } catch (error) {
      setServerError('Registration failed. Please review the inputs and try again.')
    }
  }

  return (
    <div className="flex min-h-screen items-center justify-center bg-gradient-to-br from-slate-50 via-white to-slate-100 p-4">
      <div className="w-full max-w-xl rounded-2xl border border-slate-200 bg-white/80 p-8 shadow-card backdrop-blur">
        <div className="mb-6 text-center">
          <p className="text-xs uppercase tracking-[0.2em] text-slate-500">SmartLight</p>
          <h1 className="text-2xl font-semibold text-slate-900">Create your account</h1>
          <p className="text-sm text-slate-600">Register to start managing your spaces.</p>
        </div>
        <form onSubmit={handleSubmit(onSubmit)} className="grid grid-cols-2 gap-4">
          <Input label="Username" placeholder="your.username" {...register('username')} error={errors.username?.message} />
          <Input label="Email" type="email" placeholder="you@example.com" {...register('email')} error={errors.email?.message} />
          <Input label="Phone number" placeholder="+123..." {...register('phone_number')} error={errors.phone_number?.message} />
          <div className="col-span-2 grid grid-cols-2 gap-4">
            <Input
              label="Password"
              type="password"
              placeholder="••••••••"
              {...register('password')}
              error={errors.password?.message}
            />
            <Input
              label="Confirm password"
              type="password"
              placeholder="••••••••"
              {...register('password2')}
              error={errors.password2?.message}
            />
          </div>
          {serverError && (
            <div className="col-span-2 rounded-lg bg-rose-50 px-3 py-2 text-sm text-rose-700">
              {serverError}
            </div>
          )}
          <Button type="submit" className="col-span-2" loading={isSubmitting}>
            Create account
          </Button>
        </form>
        <p className="mt-6 text-center text-sm text-slate-600">
          Have an account?{' '}
          <Link to="/login" className="font-semibold text-slate-900 underline">
            Sign in
          </Link>
        </p>
      </div>
    </div>
  )
}

