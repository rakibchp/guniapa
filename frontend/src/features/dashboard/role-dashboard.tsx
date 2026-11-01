import Link from "next/link";
import { redirect } from "next/navigation";
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

const roleContent = {
  CUSTOMER: {
    welcome: "A little help can make a big difference.",
    nextTitle: "Your next step starts here",
    nextText:
      "Service discovery and booking are not connected yet. No providers, prices or availability are shown until the API supports them.",
  },
  PROVIDER: {
    welcome: "Your skills have a place here.",
    nextTitle: "Get ready to share your skills",
    nextText:
      "Provider profile and credential workflows are not connected yet. Phone verification alone does not mean a provider or professional credential is approved.",
  },
  ADMIN: {
    welcome: "Manage the community responsibly.",
    nextTitle: "Administration and review",
    nextText:
      "Manage categories, fees, provider approvals, review moderation and support tickets in Django admin. The staff console requires its own authenticated administrator session.",
  },
} as const;

export async function RoleDashboard({
  role,
}: {
  role: UserRole;
}) {
  const user = await getSession();
  if (!user) redirect("/login");
  if (user.role !== role) redirect(roleRoutes[user.role]);
  const content = roleContent[role];

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
        <h1>{content.welcome}</h1>
        <p className="dashboard-intro">Welcome, {user.full_name}. Here’s the current status of your account.</p>

        <section className="account-card" aria-labelledby="account-status-title">
          <div>
            <div className="account-card-heading">
              <span className="status-icon" aria-hidden="true">✓</span>
              <div>
                <p className="eyebrow">ACCOUNT STATUS</p>
                <h2 id="account-status-title">{user.is_phone_verified ? "Phone verified" : "Phone verification needed"}</h2>
              </div>
            </div>
            <p className="account-card-note">
              {user.is_phone_verified
                ? "Your phone number was verified for account access."
                : "Verify your phone number to meet the current sign-in requirement."}
            </p>
          </div>
          {!user.is_phone_verified && <Link className="button button-dark" href="/verify-phone">Verify phone</Link>}
        </section>

        <section className="dashboard-next" aria-labelledby="next-steps-title">
          <div>
            <p className="eyebrow">WHAT’S NEXT</p>
            <h2 id="next-steps-title">{content.nextTitle}</h2>
          </div>
          <p>{content.nextText}</p>
          {role === "ADMIN" && (
            <Link className="button button-dark button-small" href="/admin/">
              Open Django admin
            </Link>
          )}
        </section>

        <div className="dashboard-footer">
          <Link href="/">← Back to Guniapa</Link>
          <span>Account access is managed securely by Guniapa.</span>
        </div>
      </div>
    </main>
  );
}
