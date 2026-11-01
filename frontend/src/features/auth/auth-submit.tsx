"use client";

import { useFormStatus } from "react-dom";

export function AuthSubmit({
  children,
  pendingText,
}: {
  children: React.ReactNode;
  pendingText: string;
}) {
  const { pending } = useFormStatus();
  return (
    <button className="button button-dark auth-submit" type="submit" disabled={pending}>
      {pending ? pendingText : children}
    </button>
  );
}
