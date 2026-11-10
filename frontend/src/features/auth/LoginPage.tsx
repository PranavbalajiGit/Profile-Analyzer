import { useQuery } from "@tanstack/react-query";
import { useState, type FormEvent } from "react";
import { Link, Navigate, useLocation, useNavigate } from "react-router-dom";

import { ErrorBanner, FullPageLoader } from "../../components/ui/Feedback";
import {
  inputClass,
  labelClass,
  primaryButtonClass,
  secondaryButtonClass,
} from "../../components/ui/styles";
import { errorMessage } from "../../lib/format";
import { homePathFor } from "../../lib/roles";
import { authApi } from "../../services/api";
import { useAuth } from "./AuthContext";

interface LocationState {
  from?: { pathname?: string; search?: string };
}

export function LoginPage() {
  const { user, isLoading, login } = useAuth();
  const navigate = useNavigate();
  const location = useLocation();
  const [collegeCode, setCollegeCode] = useState("");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [ssoError, setSsoError] = useState<string | null>(null);

  const config = useQuery({
    queryKey: ["auth", "config"],
    queryFn: authApi.config,
    staleTime: 5 * 60_000,
    retry: false,
  });

  if (isLoading) {
    return <FullPageLoader />;
  }

  if (user) {
    return <Navigate to={homePathFor(user)} replace />;
  }

  const state = location.state as LocationState | null;
  const requestedPath = state?.from?.pathname;

  async function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setError(null);
    setSubmitting(true);
    try {
      const account = await login({
        college_code: collegeCode.trim().toUpperCase(),
        email: email.trim(),
        password,
      });
      navigate(requestedPath ?? homePathFor(account), { replace: true });
    } catch (caught) {
      setError(errorMessage(caught));
    } finally {
      setSubmitting(false);
    }
  }

  async function handleSso() {
    setSsoError(null);
    const code = collegeCode.trim().toUpperCase();
    if (!code) {
      setSsoError("Enter your institution code first, for example NFIT.");
      return;
    }
    try {
      const started = await authApi.oidcStart(code);
      window.location.assign(started.authorization_url);
    } catch (caught) {
      setSsoError(errorMessage(caught));
    }
  }

  return (
    <main className="flex min-h-screen items-center justify-center bg-slate-50 px-4 py-12">
      <section className="w-full max-w-md rounded-xl border border-slate-200 bg-white p-8 shadow-sm">
        <div className="mb-6 flex items-center gap-3">
          <span className="flex size-11 items-center justify-center rounded-lg bg-brand-600 text-sm font-semibold text-white">
            PA
          </span>
          <div className="leading-tight">
            <p className="text-sm font-semibold text-slate-900">Profile Analyzer</p>
            <p className="text-xs text-slate-500">Institutional sign-in</p>
          </div>
        </div>

        <h1 className="text-xl font-semibold text-slate-900">Welcome back</h1>
        <p className="mt-2 text-sm text-slate-600">
          Use the institution code and account issued by your college. Access is limited to
          identities provisioned by an administrator.
        </p>

        <form className="mt-6 space-y-4" onSubmit={handleSubmit}>
          <div>
            <label className={labelClass} htmlFor="college-code">
              Institution code
            </label>
            <input
              id="college-code"
              className={inputClass}
              value={collegeCode}
              onChange={(event) => setCollegeCode(event.target.value)}
              placeholder="NFIT"
              autoComplete="organization"
              required
              maxLength={32}
            />
          </div>

          <div>
            <label className={labelClass} htmlFor="email">
              Institutional email
            </label>
            <input
              id="email"
              type="email"
              className={inputClass}
              value={email}
              onChange={(event) => setEmail(event.target.value)}
              placeholder="you@college.example.edu"
              autoComplete="username"
              required
              maxLength={320}
            />
          </div>

          <div>
            <label className={labelClass} htmlFor="password">
              Password
            </label>
            <input
              id="password"
              type="password"
              className={inputClass}
              value={password}
              onChange={(event) => setPassword(event.target.value)}
              autoComplete="current-password"
              required
              maxLength={256}
            />
          </div>

          {error ? <ErrorBanner message={error} /> : null}

          <button type="submit" className={`${primaryButtonClass} w-full`} disabled={submitting}>
            {submitting ? "Signing in…" : "Sign in"}
          </button>
        </form>

        {config.data?.oidc_enabled ? (
          <div className="mt-4 space-y-3">
            <div className="flex items-center gap-3 text-xs uppercase tracking-wider text-slate-400">
              <span className="h-px flex-1 bg-slate-200" />
              or
              <span className="h-px flex-1 bg-slate-200" />
            </div>
            <button type="button" className={`${secondaryButtonClass} w-full`} onClick={handleSso}>
              Continue with institutional SSO
            </button>
            {ssoError ? <ErrorBanner message={ssoError} /> : null}
          </div>
        ) : null}

        <p className="mt-6 text-center text-xs text-slate-500">
          Route guards are a UX convenience, never a security boundary. Every request is
          authorized by the API and constrained by PostgreSQL row-level security.
        </p>

        <p className="mt-3 text-center text-xs">
          <Link className="text-brand-700 hover:underline" to="/">
            Return to the home redirect
          </Link>
        </p>
      </section>
    </main>
  );
}
