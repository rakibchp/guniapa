import type { Metadata } from "next";
import Link from "next/link";
import { AuthShell } from "@/features/auth/auth-shell";
import { LoginForm } from "@/features/auth/auth-forms";

export const metadata: Metadata = { title: "Log in" };

export default async function LoginPage({
  searchParams,
}: {
  searchParams: Promise<{ verified?: string; logout?: string; expired?: string }>;
}) {
  const params = await searchParams;
  const notice =
    params.verified === "1"
      ? "Your phone number is verified. You can now log in."
      : params.logout === "done"
        ? "You’ve been logged out."
        : params.logout === "unconfirmed"
          ? "This device has been logged out, but the server could not confirm token revocation."
          : params.expired === "1"
            ? "Your session expired. Sign in again to continue."
            : undefined;

  return (
    <AuthShell
      eyebrow="WELCOME BACK"
      title="Log in to Guniapa"
      description="Sign in to continue to your Guniapa account."
      footer={<>New to Guniapa? <Link href="/register">Create an account</Link></>}
    >
      <LoginForm notice={notice} />
    </AuthShell>
  );
}
