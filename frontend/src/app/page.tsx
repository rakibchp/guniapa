import Link from "next/link";

const services = [
  { icon: "⌂", name: "Home services", detail: "Cleaning, cooking, laundry" },
  { icon: "♡", name: "Care & wellness", detail: "Thoughtful, trusted support" },
  { icon: "✳", name: "Learning", detail: "Tutoring and teaching" },
  { icon: "✦", name: "Personal care", detail: "Beauty and grooming" },
];

const steps = [
  { number: "01", title: "Find the right help", text: "Explore local skills and choose the service that fits your day." },
  { number: "02", title: "Agree on the details", text: "Share what you need, where and when. Review the plan before you confirm." },
  { number: "03", title: "Build trust together", text: "Keep communication clear and share feedback after the work is done." },
];

export default function Home() {
  return (
    <main>
      <header className="site-header">
        <div className="container nav-wrap">
          <Link className="brand" href="/" aria-label="Guniapa home">
            <span className="brand-mark" aria-hidden="true">g</span>
            <span>guniapa<span className="brand-dot">.</span></span>
          </Link>
          <nav className="desktop-nav" aria-label="Main navigation">
            <a href="#services">Explore services</a>
            <a href="#how-it-works">How it works</a>
            <a href="#providers">For providers</a>
          </nav>
          <div className="nav-actions">
            <Link className="nav-login" href="/login">Log in</Link>
            <Link className="button button-small button-dark" href="/register">Get started <span aria-hidden="true">↗</span></Link>
          </div>
        </div>
      </header>

      <section className="hero">
        <div className="container hero-grid">
          <div className="hero-copy">
            <div className="eyebrow"><span className="eyebrow-dot" /> MADE FOR YOUR NEIGHBOURHOOD</div>
            <h1>Good people.<br /><span>Good work.</span><br />Right nearby.</h1>
            <p className="hero-description">
              Find skilled local service providers, or grow your own work with a community that values what you do.
            </p>
            <div className="hero-actions">
              <Link className="button button-dark" href="/register?role=CUSTOMER">Join as a customer <span aria-hidden="true">↗</span></Link>
              <Link className="button button-outline" href="/register?role=PROVIDER">Join as a provider</Link>
            </div>
            <div className="hero-note">
              <span className="note-icon" aria-hidden="true">✳</span>
              <span>Local skills. Trusted help. More opportunity.</span>
            </div>
          </div>

          <div className="hero-art" aria-label="Illustration of neighbours connecting through local services">
            <div className="art-sun" />
            <div className="art-label"><span className="art-pulse" /> GOOD WORK, CLOSE TO HOME</div>
            <div className="art-arch">
              <div className="art-window">
                <div className="window-sky" />
                <div className="window-plant plant-one" />
                <div className="window-plant plant-two" />
                <div className="window-table" />
              </div>
              <div className="person person-left">
                <div className="person-hair" />
                <div className="person-head"><span className="person-face" /></div>
                <div className="person-body"><span className="body-detail" /></div>
                <div className="person-arm" />
              </div>
              <div className="person person-right">
                <div className="person-hair" />
                <div className="person-head"><span className="person-face" /></div>
                <div className="person-body"><span className="body-detail" /></div>
                <div className="person-arm" />
              </div>
              <div className="art-spark spark-one">✳</div>
              <div className="art-spark spark-two">✦</div>
            </div>
            <div className="art-card art-card-top">
              <span className="mini-icon mini-icon-coral">⌂</span>
              <span><strong>Helpful, close by</strong><small>Made for local communities</small></span>
            </div>
            <div className="art-card art-card-bottom">
              <span className="mini-icon mini-icon-green">♡</span>
              <span><strong>Skills deserve to grow</strong><small>Discover a new opportunity</small></span>
            </div>
            <div className="art-ground" />
          </div>
        </div>
      </section>

      <section className="service-section" id="services">
        <div className="container">
          <div className="section-heading">
            <div>
              <p className="eyebrow">A LITTLE HELP GOES A LONG WAY</p>
              <h2>A community for local skills.</h2>
            </div>
            <p className="section-intro">Examples of service areas Guniapa is being built to support.</p>
          </div>
          <div className="service-grid">
            {services.map((service, index) => (
              <article className={`service-card service-card-${index + 1}`} key={service.name}>
                <span className="service-icon" aria-hidden="true">{service.icon}</span>
                <span className="service-title">{service.name}</span>
                <span className="service-detail">{service.detail}</span>
              </article>
            ))}
          </div>
          <p className="catalog-note">These are examples, not live listings. Service discovery will be available when the catalog API is connected.</p>
        </div>
      </section>

      <section className="how-section" id="how-it-works">
        <div className="container how-grid">
          <div className="how-heading">
            <p className="eyebrow">SIMPLE BY DESIGN</p>
            <h2>From “I need a hand” to <span>“all taken care of.”</span></h2>
            <p>Clear expectations make good work better for everyone.</p>
          </div>
          <ol className="steps-list">
            {steps.map((step) => (
              <li className="step" key={step.number}>
                <span className="step-number">{step.number}</span>
                <div><h3>{step.title}</h3><p>{step.text}</p></div>
              </li>
            ))}
          </ol>
        </div>
      </section>

      <section className="provider-section" id="providers">
        <div className="container provider-banner">
          <div className="provider-decoration" aria-hidden="true"><span>✳</span><span>✦</span><span>♡</span></div>
          <div className="provider-copy">
            <p className="eyebrow">YOUR SKILLS HAVE VALUE</p>
            <h2>Make room for<br />more opportunity.</h2>
            <p>Build your profile, share the work you do and connect with people looking for your skills.</p>
            <Link className="button button-light" href="/register?role=PROVIDER">Join as a provider <span aria-hidden="true">↗</span></Link>
          </div>
          <div className="provider-side-note">
            <span className="side-note-mark">g.</span>
            <p>Good work deserves<br />to be seen.</p>
            <span className="side-note-line" />
            <small>GUNIAPA COMMUNITY</small>
          </div>
        </div>
      </section>

      <section className="trust-section">
        <div className="container trust-grid">
          <div><p className="eyebrow">BUILT AROUND PEOPLE</p><h2>Trust starts with<br />clear expectations.</h2></div>
          <div className="trust-item"><span className="trust-icon">01</span><div><h3>Know who you’re meeting</h3><p>Accounts can verify a phone number before signing in. Verification status is shown accurately.</p></div></div>
          <div className="trust-item"><span className="trust-icon">02</span><div><h3>Your details stay yours</h3><p>Share service and contact information only when it’s needed to arrange your work.</p></div></div>
          <div className="trust-item"><span className="trust-icon">03</span><div><h3>Room to speak up</h3><p>We’re building a service where both customers and providers can be heard.</p></div></div>
        </div>
      </section>

      <footer className="site-footer">
        <div className="container footer-main">
          <div><Link className="brand footer-brand" href="/"><span className="brand-mark" aria-hidden="true">g</span><span>guniapa<span className="brand-dot">.</span></span></Link><p>Local skills. Trusted help.<br />More opportunity.</p></div>
          <div className="footer-links"><a href="#services">Explore services</a><a href="#how-it-works">How it works</a><a href="#providers">Become a provider</a><Link href="/login">Log in</Link></div>
          <Link className="button button-small button-dark" href="/register">Join the community <span aria-hidden="true">↗</span></Link>
        </div>
        <div className="container footer-bottom"><span>© Guniapa</span><span>Made for the people who make a difference.</span><span>Bangladesh · BDT ৳</span></div>
      </footer>
    </main>
  );
}
