import { FormEvent, useState } from 'react';
import { login } from '../api';

interface LoginPanelProps {
  onToken: (token: string) => void;
}

export default function LoginPanel({ onToken }: LoginPanelProps): JSX.Element {
  const [email, setEmail] = useState('user@edms.local');
  const [password, setPassword] = useState('user123');
  const [error, setError] = useState<string | null>(null);
  const [isSubmitting, setIsSubmitting] = useState(false);

  async function handleSubmit(event: FormEvent<HTMLFormElement>): Promise<void> {
    event.preventDefault();
    setError(null);
    setIsSubmitting(true);

    try {
      const result = await login(email, password);
      onToken(result.access_token);
    } catch (submitError) {
      setError(submitError instanceof Error ? submitError.message : 'Login failed');
    } finally {
      setIsSubmitting(false);
    }
  }

  return (
    <section className="card">
      <h2>Sign in</h2>
      <p className="hint">Demo account: user@edms.local / user123</p>



      <form onSubmit={handleSubmit} className="stack">
        <label>
          Email
          <input value={email} onChange={(e) => setEmail(e.target.value)} required />
        </label>

        <label>
          Password
          <input
            type="password"
            value={password}
            onChange={(e) => setPassword(e.target.value)}
            required
          />
        </label>

        <button type="submit" disabled={isSubmitting}>
          {isSubmitting ? 'Signing in…' : 'Sign in'}
        </button>
      </form>

      {error ? <p className="error">{error}</p> : null}
    </section>
  );
}
