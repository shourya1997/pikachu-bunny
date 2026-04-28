import { supabase } from '../lib/supabase'

export function LoginPage() {
  async function signIn() {
    await supabase.auth.signInWithOAuth({
      provider: 'google',
      options: { redirectTo: window.location.origin },
    })
  }

  return (
    <div style={{ padding: 32, textAlign: 'center' }}>
      <h1>AuditOS</h1>
      <p>Audit your EPF contributions in 60 seconds.</p>
      <button onClick={signIn}>Sign in with Google</button>
    </div>
  )
}
