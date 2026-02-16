import { FormEvent, useState } from "react";
import { login } from "../api";
import Banner from "./ui/Banner";
import Button from "./ui/Button";
import Card from "./ui/Card";
import Input from "./ui/Input";

interface LoginPanelProps {
  onToken: (token: string) => void;
}

export default function LoginPanel({ onToken }: LoginPanelProps): JSX.Element {
  const [email, setEmail] = useState("user@edms.local");
  const [password, setPassword] = useState("user123");
  const [error, setError] = useState<string | null>(null);
  const [isSubmitting, setIsSubmitting] = useState(false);

  async function handleSubmit(
    event: FormEvent<HTMLFormElement>,
  ): Promise<void> {
    event.preventDefault();
    setError(null);
    setIsSubmitting(true);

    try {
      const result = await login(email, password);
      onToken(result.access_token);
    } catch (submitError) {
      setError(
        submitError instanceof Error ? submitError.message : "Login failed",
      );
    } finally {
      setIsSubmitting(false);
    }
  }

  return (
    <Card
      title="Sign in"
      subtitle="Use the demo user account to access the EDMS workspace."
    >
      <form onSubmit={handleSubmit} className="stack">
        <Input
          label="Email"
          value={email}
          onChange={(e) => setEmail(e.target.value)}
          required
        />
        <Input
          label="Password"
          type="password"
          value={password}
          onChange={(e) => setPassword(e.target.value)}
          required
        />

        <Button type="submit" disabled={isSubmitting}>
          {isSubmitting ? "Signing in…" : "Sign in"}
        </Button>
      </form>

      {error ? <Banner tone="error" message={error} /> : null}
    </Card>
  );
}
