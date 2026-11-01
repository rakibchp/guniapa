import type { Metadata } from "next";
import Link from "next/link";
import { AuthShell } from "@/features/auth/auth-shell";
import { RegisterForm } from "@/features/auth/auth-forms";

export const metadata: Metadata = { title: "Create an account" };

export default async function RegisterPage({
  searchParams,
}: {
  searchParams: Promise<{ role?: string }>;
}) {
  const { role = "" } = await searchParams;

  return (
    <AuthShell
      eyebrow="JOIN THE COMMUNITY"
      title="Create your account"
      description="Start with the basics. You’ll verify your phone number before signing in."
      footer={<>Already have an account? <Link href="/login">Log in</Link></>}
    >
      <RegisterForm initialRole={role} />
    </AuthShell>
  );
}
