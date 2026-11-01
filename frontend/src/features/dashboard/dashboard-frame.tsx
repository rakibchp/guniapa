import Link from "next/link";
import { redirect } from "next/navigation";
import type { ReactNode } from "react";
import { signOutAction } from "@/features/auth/actions";
import { getSession, type UserRole } from "@/lib/session";

const roleLabels = {
  CUSTOMER: "Customer",
  PROVIDER: "Service provider",
  ADMIN: "Administrator",
} as const;

const roleRoutes = {
  CUSTOMER: "/dashboard/customer",
  PROVIDER: "/dashboard/provider",
  ADMIN: "/dashboard/admin",
} as const;

export async function DashboardFrame({
  role,
  title,
  children,
}: {
  role: UserRole;
  title: string;
  children: ReactNode;
}) {
  const user = await getSession();
  if (!user) redirect("/login");
  if (user.role !== role) redirect(roleRoutes[user.role]);

  return (
    <main className="dashboard-page">
      <header className="dashboard-header">
        <div className="container dashboard-header-inner">
          <Link className="brand" href="/" aria-label="Guniapa home">
            <span className="brand-mark" aria-hidden="true">g</span>
            <span>guniapa<span className="brand-dot">.</span></span>
          </Link>
          <div className="dashboard-user">
            <span className="dashboard-user-name">{user.full_name}</span>
            <span className="role-pill">{roleLabels[user.role]}</span>
            <form action={signOutAction}>
              <button className="text-button" type="submit">Log out</button>
            </form>
          </div>
        </div>
      </header>
      <div className="container dashboard-content">
        <p className="eyebrow">YOUR GUNIAPA ACCOUNT</p>
        <h1>{title}</h1>
        <p className="dashboard-intro">Welcome, {user.full_name}. Here’s your account activity.</p>
        {children}
        <div className="dashboard-footer">
          <Link href="/">← Back to Guniapa</Link>
          <span>Account access is managed securely by Guniapa.</span>
        </div>
      </div>
    </main>
  );
}
