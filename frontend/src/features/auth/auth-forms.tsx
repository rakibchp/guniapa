"use client";

import Link from "next/link";
import { useActionState } from "react";
import {
  loginAction,
  registerAction,
  sendOtpAction,
  verifyOtpAction,
  type AuthActionState,
} from "@/features/auth/actions";
import { AuthSubmit } from "@/features/auth/auth-submit";

const emptyState: AuthActionState = {};

function FormMessage({
  error,
  info,
}: {
  error?: string;
  info?: string;
}) {
  if (error) return <p className="form-message form-error" role="alert">{error}</p>;
  if (info) return <p className="form-message form-info" role="status">{info}</p>;
  return null;
}

export function LoginForm({ notice }: { notice?: string }) {
  const [state, action] = useActionState(loginAction, emptyState);
  return (
    <>
      {notice && <p className="form-message form-info" role="status">{notice}</p>}
      <form className="auth-form" action={action}>
        <label className="field">
          <span>Email or phone number</span>
          <input
            autoComplete="username"
            name="identifier"
            placeholder="you@example.com or +880..."
            required
          />
        </label>
        <label className="field">
          <span>Password</span>
          <input
            autoComplete="current-password"
            name="password"
            type="password"
            required
          />
        </label>
        <FormMessage error={state.error} />
        <AuthSubmit pendingText="Signing in…">Log in <span aria-hidden="true">↗</span></AuthSubmit>
      </form>
      <p className="auth-hint">New here? <Link href="/register">Create an account</Link></p>
      <p className="auth-hint">Need to verify your phone? <Link href="/verify-phone">Verify your number</Link></p>
    </>
  );
}

export function RegisterForm({ initialRole }: { initialRole: string }) {
  const [state, action] = useActionState(registerAction, emptyState);
  const defaultRole = initialRole === "PROVIDER" ? "PROVIDER" : "CUSTOMER";
  return (
    <form className="auth-form" action={action}>
      <label className="field">
        <span>Your name</span>
        <input autoComplete="name" maxLength={150} name="full_name" required />
      </label>
      <label className="field">
        <span>Email address</span>
        <input autoComplete="email" name="email" type="email" required />
      </label>
      <label className="field">
        <span>Phone number</span>
        <input
          autoComplete="tel"
          inputMode="tel"
          name="phone_number"
          placeholder="+8801XXXXXXXXX"
          pattern="^\+?[1-9]\d{7,14}$"
          required
        />
        <small>Use international format. You’ll verify this number next.</small>
      </label>
      <label className="field">
        <span>I’m joining as</span>
        <select defaultValue={defaultRole} name="role">
          <option value="CUSTOMER">Customer — I’m looking for a service</option>
          <option value="PROVIDER">Provider — I’m offering my skills</option>
        </select>
      </label>
      <label className="field">
        <span>Password</span>
        <input
          autoComplete="new-password"
          minLength={8}
          name="password"
          type="password"
          required
        />
        <small>Use at least 8 characters. Stronger passwords are recommended.</small>
      </label>
      <FormMessage error={state.error} />
      <AuthSubmit pendingText="Creating account…">Create account <span aria-hidden="true">↗</span></AuthSubmit>
    </form>
  );
}

export function SendOtpForm({ phoneNumber }: { phoneNumber: string }) {
  const [state, action] = useActionState(sendOtpAction, emptyState);
  return (
    <form className="auth-form otp-form" action={action}>
      <label className="field">
        <span>Phone number</span>
        <input
          autoComplete="tel"
          inputMode="tel"
          name="phone_number"
          defaultValue={phoneNumber}
          placeholder="+8801XXXXXXXXX"
          pattern="^\+?[1-9]\d{7,14}$"
          required
        />
      </label>
      <FormMessage error={state.error} info={state.info} />
      <AuthSubmit pendingText="Sending code…">Send verification code</AuthSubmit>
    </form>
  );
}

export function VerifyOtpForm({ phoneNumber }: { phoneNumber: string }) {
  const [state, action] = useActionState(verifyOtpAction, emptyState);
  return (
    <form className="auth-form" action={action}>
      <label className="field">
        <span>Phone number</span>
        <input
          autoComplete="tel"
          inputMode="tel"
          name="phone_number"
          defaultValue={phoneNumber}
          placeholder="+8801XXXXXXXXX"
          pattern="^\+?[1-9]\d{7,14}$"
          required
        />
      </label>
      <label className="field">
        <span>6-digit verification code</span>
        <input
          autoComplete="one-time-code"
          inputMode="numeric"
          maxLength={6}
          minLength={6}
          name="otp"
          pattern="\d{6}"
          required
        />
      </label>
      <FormMessage error={state.error} />
      <AuthSubmit pendingText="Verifying…">Verify phone number <span aria-hidden="true">↗</span></AuthSubmit>
    </form>
  );
}
