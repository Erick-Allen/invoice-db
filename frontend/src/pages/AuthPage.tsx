import { useState } from "react";
import { useNavigate } from "react-router-dom";
import { login, signup, type AuthUser } from "../api/auth";

type AuthMode = "signin" | "signup";

type AuthPageProps = {
  onAuthSuccess: (user: AuthUser) => void;
};

export function AuthPage({ onAuthSuccess }: AuthPageProps) {
  const navigate = useNavigate();
  const [authMode, setAuthMode] = useState<AuthMode>("signin");
  const [email, setEmail] = useState("");
  const [name, setName] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState("");
  const [isSubmitting, setIsSubmitting] = useState(false);
  const isSignUp = authMode === "signup";

  function handleModeChange(nextMode: AuthMode) {
    setAuthMode(nextMode);
    setError("");
  }

  async function handleSubmit(event: React.FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setError("");
    setIsSubmitting(true);

    try {
      const response = isSignUp
        ? await signup({ email, password, name })
        : await login({ email, password });

      onAuthSuccess(response.user);
      navigate("/");
    } catch (error) {
      setError(error instanceof Error ? error.message : "Authentication failed.");
    } finally {
      setIsSubmitting(false);
    }
  }

  return (
    <section className="auth-page">
      <div className="auth-card">
        <div className="auth-copy">
          <h2>Sign in to save your own invoice data.</h2>
          <p>Use an account when you want changes to persist.</p>
        </div>

        <div className="auth-mode-toggle" aria-label="Choose auth mode">
          <button
            className={!isSignUp ? "active" : ""}
            type="button"
            onClick={() => handleModeChange("signin")}
          >
            Sign In
          </button>
          <button
            className={isSignUp ? "active" : ""}
            type="button"
            onClick={() => handleModeChange("signup")}
          >
            Sign Up
          </button>
        </div>

        <form className="auth-form" onSubmit={handleSubmit}>
          {error && <p className="error-message">{error}</p>}

          <div className="form-field">
            <label htmlFor="auth-email">Email</label>
            <input
              id="auth-email"
              name="email"
              type="email"
              autoComplete="email"
              placeholder="you@example.com"
              required
              value={email}
              onChange={(event) => setEmail(event.target.value)}
            />
          </div>

          {isSignUp && (
            <div className="form-field">
              <label htmlFor="auth-name">Name</label>
              <input
                id="auth-name"
                name="name"
                  type="text"
                  autoComplete="name"
                  placeholder="Your name"
                  value={name}
                  onChange={(event) => setName(event.target.value)}
                />
              </div>
            )}

          <div className="form-field">
            <label htmlFor="auth-password">Password</label>
            <input
              id="auth-password"
              name="password"
              type="password"
              autoComplete={isSignUp ? "new-password" : "current-password"}
              required
              value={password}
              onChange={(event) => setPassword(event.target.value)}
            />
          </div>

          <button className="primary-button auth-submit-button" type="submit" disabled={isSubmitting}>
            {isSubmitting ? "Working..." : isSignUp ? "Create Account" : "Sign In"}
          </button>
        </form>
      </div>
    </section>
  );
}
