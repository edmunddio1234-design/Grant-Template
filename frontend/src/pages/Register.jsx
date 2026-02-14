import { useState } from 'react'
import { useNavigate, Link } from 'react-router-dom'
import { UserPlus, Eye, EyeOff, ArrowLeft } from 'lucide-react'
import toast from 'react-hot-toast'
import { apiClient } from '../api/client'
import useAuthStore from '../stores/authStore'

export default function Register() {
  const navigate = useNavigate()
  const { login } = useAuthStore()
  const [form, setForm] = useState({
    name: '',
    email: '',
    password: '',
    confirmPassword: '',
  })
  const [showPassword, setShowPassword] = useState(false)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')

  const updateField = (field) => (e) =>
    setForm((prev) => ({ ...prev, [field]: e.target.value }))

  const passwordsMatch = form.password === form.confirmPassword
  const passwordLongEnough = form.password.length >= 8
  const formValid =
    form.name && form.email && form.password && form.confirmPassword && passwordsMatch && passwordLongEnough

  const handleSubmit = async (e) => {
    e.preventDefault()
    setError('')

    if (!passwordsMatch) {
      setError('Passwords do not match.')
      return
    }
    if (!passwordLongEnough) {
      setError('Password must be at least 8 characters.')
      return
    }

    setLoading(true)

    try {
      // Register the new account
      await apiClient.register(form.email, form.name, form.password, 'viewer')

      // Auto-login after successful registration
      const res = await apiClient.login(form.email, form.password)
      const { access_token, refresh_token } = res.data

      const meRes = await apiClient.getMe(access_token)
      const user = meRes.data

      login(user, access_token, refresh_token)
      toast.success(`Welcome, ${user.name}! Your account has been created.`)
      navigate('/')
    } catch (err) {
      const message =
        err.response?.data?.detail || 'Registration failed. Please try again.'
      setError(typeof message === 'string' ? message : JSON.stringify(message))
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="min-h-screen flex items-center justify-center bg-gradient-to-br from-gray-50 to-gray-100">
      <div className="w-full max-w-md">
        {/* Logo / Brand */}
        <div className="text-center mb-8">
          <div className="inline-flex items-center justify-center w-16 h-16 bg-foam-primary rounded-2xl mb-4">
            <span className="text-white font-bold text-2xl">FM</span>
          </div>
          <h1 className="text-2xl font-bold text-gray-900">Create an Account</h1>
          <p className="text-gray-500 mt-2">
            Join the Grant Alignment Engine
          </p>
        </div>

        {/* Registration Card */}
        <div className="bg-white rounded-xl shadow-lg border border-gray-200 p-8">
          <form onSubmit={handleSubmit} className="space-y-4">
            {error && (
              <div className="p-3 bg-red-50 border border-red-200 rounded-lg">
                <p className="text-sm text-red-700">{error}</p>
              </div>
            )}

            {/* Full Name */}
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Full Name
              </label>
              <input
                type="text"
                value={form.name}
                onChange={updateField('name')}
                placeholder="e.g. Sonny Robinson"
                required
                autoFocus
                className="w-full px-4 py-2.5 border border-gray-300 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-foam-primary focus:border-transparent"
              />
            </div>

            {/* Email */}
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Email Address
              </label>
              <input
                type="email"
                value={form.email}
                onChange={updateField('email')}
                placeholder="you@example.org"
                required
                className="w-full px-4 py-2.5 border border-gray-300 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-foam-primary focus:border-transparent"
              />
            </div>

            {/* Password */}
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Password
              </label>
              <div className="relative">
                <input
                  type={showPassword ? 'text' : 'password'}
                  value={form.password}
                  onChange={updateField('password')}
                  placeholder="Min. 8 characters"
                  required
                  minLength={8}
                  className="w-full px-4 py-2.5 border border-gray-300 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-foam-primary focus:border-transparent pr-10"
                />
                <button
                  type="button"
                  onClick={() => setShowPassword(!showPassword)}
                  className="absolute right-3 top-1/2 -translate-y-1/2 text-gray-400 hover:text-gray-600"
                >
                  {showPassword ? <EyeOff size={18} /> : <Eye size={18} />}
                </button>
              </div>
              {form.password && !passwordLongEnough && (
                <p className="text-xs text-amber-600 mt-1">
                  Password must be at least 8 characters
                </p>
              )}
            </div>

            {/* Confirm Password */}
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Confirm Password
              </label>
              <input
                type={showPassword ? 'text' : 'password'}
                value={form.confirmPassword}
                onChange={updateField('confirmPassword')}
                placeholder="Re-enter your password"
                required
                className={`w-full px-4 py-2.5 border rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-foam-primary focus:border-transparent ${
                  form.confirmPassword && !passwordsMatch
                    ? 'border-red-400'
                    : 'border-gray-300'
                }`}
              />
              {form.confirmPassword && !passwordsMatch && (
                <p className="text-xs text-red-600 mt-1">Passwords do not match</p>
              )}
            </div>

            {/* Submit */}
            <button
              type="submit"
              disabled={loading || !formValid}
              className="w-full flex items-center justify-center gap-2 px-4 py-2.5 bg-foam-primary text-white font-semibold rounded-lg hover:bg-foam-primary/90 transition-colors disabled:opacity-50 disabled:cursor-not-allowed mt-2"
            >
              {loading ? (
                <span className="animate-spin w-5 h-5 border-2 border-white border-t-transparent rounded-full" />
              ) : (
                <UserPlus size={18} />
              )}
              {loading ? 'Creating Account...' : 'Create Account'}
            </button>
          </form>

          {/* Back to Login */}
          <div className="mt-6 pt-6 border-t border-gray-100 text-center">
            <Link
              to="/login"
              className="inline-flex items-center gap-1 text-sm text-foam-primary hover:underline font-medium"
            >
              <ArrowLeft size={16} />
              Already have an account? Sign in
            </Link>
          </div>
        </div>
      </div>
    </div>
  )
}
