import { FormEvent, useState } from 'react';
import { login } from '../api';
import type { Role } from '../types';

const roles: Role[] = ['viewer', 'engineer', 'approver', 'admin'];

interface LoginPanelProps {
  onToken: (token: string) => void;
}

export default function LoginPanel({ onToken }: LoginPanelProps): JSX.Element {
  const [username, setUsername] = useState('alice');
  const [role, setRole] = useState<Role>('engineer');
  const [error, setError] = useState<string | null>(null);
  const [isSubmitting, setIsSubmitting] = useState(false);

  async function handleSubmit(event: FormEvent<HTMLFormElement>): Promise<void> {
    event.preventDefault();
    setError(null);
    setIsSubmitting(true);

    try {
      const result = await login(username, role);
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
      <p className="hint">Use demo auth to load dashboard and search data from the API.</p>
      <form onSubmit={handleSubmit} className="stack">
        <label>
          Username
          <input
            value={username}
            onChange={(event) => setUsername(event.target.value)}
            placeholder="alice"
            required
          />
        </label>

        <label>
          Role
          <select value={role} onChange={(event) => setRole(event.target.value as Role)}>
            {roles.map((item) => (
              <option key={item} value={item}>
                {item}
              </option>
            ))}
          </select>
        </label>

        <button type="submit" disabled={isSubmitting}>
          {isSubmitting ? 'Signing in…' : 'Sign in'}
        </button>
      </form>
      {error ? <p className="error">{error}</p> : null}
    </section>
  );
}
