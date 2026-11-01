import Link from "next/link";

type AuthShellProps = {
  eyebrow: string;
  title: string;
  description: string;
  children: React.ReactNode;
  footer: React.ReactNode;
};

export function AuthShell({
  eyebrow,
  title,
  description,
  children,
  footer,
}: AuthShellProps) {
  return (
    <main className="auth-page">
      <div className="auth-container">
        <Link className="brand auth-brand" href="/" aria-label="Guniapa home">
          <span className="brand-mark" aria-hidden="true">g</span>
          <span>guniapa<span className="brand-dot">.</span></span>
        </Link>
        <div className="auth-grid">
          <aside className="auth-aside">
            <p className="eyebrow">LOCAL SKILLS. TRUSTED HELP.</p>
            <h2>Good work<br />starts with<br /><span>good people.</span></h2>
            <p>Find the right help for your day, or let more people discover the work you do.</p>
            <div className="auth-aside-mark" aria-hidden="true">✳</div>
            <span className="auth-aside-caption">MADE FOR OUR COMMUNITY</span>
          </aside>
          <section className="auth-panel" aria-labelledby="auth-title">
            <p className="eyebrow">{eyebrow}</p>
            <h1 id="auth-title">{title}</h1>
            <p className="auth-description">{description}</p>
            {children}
            <div className="auth-footer">{footer}</div>
          </section>
        </div>
        <p className="auth-legal">By continuing, you agree to use Guniapa respectfully and keep account details private.</p>
      </div>
    </main>
  );
}
