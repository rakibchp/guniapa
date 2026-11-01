import type { Metadata } from "next";
import Link from "next/link";
import { AuthShell } from "@/features/auth/auth-shell";
import { SendOtpForm, VerifyOtpForm } from "@/features/auth/auth-forms";

export const metadata: Metadata = { title: "Verify your phone" };

export default async function VerifyPhonePage({
  searchParams,
}: {
  searchParams: Promise<{ phone?: string }>;
}) {
  const { phone = "" } = await searchParams;

  return (
    <AuthShell
      eyebrow="ONE QUICK CHECK"
      title="Verify your phone"
      description="A verified phone number helps protect your account. Request a code, then enter it below."
      footer={<>Already verified? <Link href="/login">Log in</Link></>}
    >
      <div className="verification-steps">
        <SendOtpForm phoneNumber={phone} />
        <div className="verification-divider"><span>THEN ENTER YOUR CODE</span></div>
        <VerifyOtpForm phoneNumber={phone} />
      </div>
    </AuthShell>
  );
}
