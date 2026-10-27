
# guniapa
Part Time/OnCall Local Service Provider Solution application using Python &amp; React

### Details at below: 

Guniapa — Skill at Your Service
<p align="center">
  <strong>Local skills. Trusted help. More opportunity.</strong>
</p>

Guniapa is a planned service marketplace that connects people and organizations who need trusted, on-demand or part-time help with skilled women service providers. The name combines “Guni” (গুণী — skilled/talented) and “Apa” (আপা — sister), expressing respect for the people whose skills keep homes, workplaces and communities running.
Project status: In development / concept-to-MVP. Features described here are planned and should not be interpreted as already live.

Website: https://guniapa.com
Repository: guniapa
Initial market: Bangladesh, with an architecture that can expand to additional regions.
The problem
Finding reliable help for a specific task, at a suitable time and location, can be difficult. Skilled workers may also struggle to find customers, build a trusted reputation, and receive fair, predictable work opportunities.

Guniapa aims to make service discovery and booking easier while giving providers a profile, transparent work history, and a way to grow their customer base.
The solution
Customers create a service request, choose a category and describe the task, time, budget and location. Eligible providers can review and accept suitable requests. The provider travels to the agreed location, performs the service, and the customer completes payment. Both parties can then rate and review the experience.

The experience is inspired by ride-hailing request flows, adapted for services that may be time-based, task-based, scheduled, recurring, or on-call.
Service categories
Categories should be configurable by administrators, with subcategories and eligibility requirements. Initial examples include:
- Home services: cooking, cleaning, laundry, gardening and household assistance
- Care: childcare, daycare support and elder care
- Health and wellness: nursing, physiotherapy, massage and therapy services
- Education: tutoring, teaching and learning support
- Personal care: beauty and grooming services
- Arts and events: dance, singing and other performance services
- Business and workplace support: office assistance and approved factory or commercial tasks
The platform must distinguish regulated services from general services. Nursing, therapy, childcare and similar services may require verified credentials, licensing checks, age or training requirements, and additional safeguards before a provider can offer them.
How it works
1. Create an account: Customers and providers register using supported contact details and complete the required verification steps.
2. Build a profile: Providers choose approved categories, describe their skills, set availability, service areas and pricing, and submit any required evidence.
3. Request a service: A customer selects the task, service location, preferred time, pricing method and any relevant instructions.
4. Find a suitable provider: The platform filters eligible providers by service, location, availability, trust status and other relevant factors.
5. Accept and coordinate: A provider accepts the request. The customer can see booking status and relevant trip/location updates.
6. Complete the work: Both parties confirm completion. The app supports an appropriate dispute flow if either party disagrees.
7. Pay and review: Payment can support cash and, once integrated and approved, Bangladesh mobile financial services such as bKash, Nagad and Rocket, plus supported bank/card methods.
8. Build a reputation: Verified completed jobs contribute to reviews and provider performance signals, subject to fraud prevention and fairness rules.
Planned product capabilities
Customer experience
- Service discovery, category/subcategory browsing and search
- Location-based provider discovery and map directions
- One-time, scheduled, recurring and on-call requests
- Time-based and task-based pricing
- Booking status, notifications and service history
- Cash and supported digital payments
- Ratings, reviews, tips, offers and receipts
- Reporting, cancellation, refunds and dispute support
Provider experience
- Skills, service categories, service area and availability
- Pricing and service request management
- Booking calendar and work history
- Earnings, fees, tips and payment summaries
- Customer reviews and a transparent performance dashboard
- Optional work evidence uploads, where appropriate and consented to
- Safety controls, reporting and support
Trust, safety and administration
- Role-based access control for customers, providers, support agents and administrators
- Phone/SIM ownership verification, email verification and identity verification
- Additional credential checks for regulated services
- Booking audit trail, fraud controls, abuse reporting and moderation
- Configurable categories, service fees, offers and regional settings
- Refunds, complaints, incident handling and account appeals
- Privacy controls and retention rules for identity documents and uploaded media
Proposed initial fees
The current business concept proposes:
- A one-time account opening charge of ৳100 for a customer and ৳100 for a provider
- A ৳10 customer service fee per successfully completed service
- A ৳10 provider service fee per successfully completed service
These are proposed business rules, not confirmed payment functionality. Before launch, validate the fees with users and review applicable Bangladesh laws, payment-provider terms, tax obligations, refund rules and consumer-protection requirements. Show all fees clearly before a user confirms a booking. Do not charge a completion fee for a cancelled or uncompleted service unless a clearly disclosed, legally reviewed policy specifically allows it.
Technology direction
The first release should be a secure modular application rather than a premature microservices system.
- Frontend: React, TypeScript, a responsive UI and accessible components
- Backend: Python with Django REST Framework or FastAPI (choose one for the MVP; avoid running both without a clear need)
- Database: PostgreSQL as the source of truth
- Cache and short-lived coordination: Redis, introduced where measurements justify it
- Background work: Celery with Redis or RabbitMQ, when asynchronous jobs are needed
- Maps: A map/geocoding provider selected after cost, coverage, privacy and licensing review
- Authentication: Short-lived access tokens or secure server sessions, refresh-token rotation where applicable, and role/permission checks on the backend
- Deployment later: Docker, a reverse proxy such as NGINX, automated tests and CI/CD; cloud hosting can be selected after the MVP is complete
Kafka, Kubernetes and multi-service deployment are possible future options, not requirements for the first release.
Security and privacy principles
- Never store passwords in plain text; use a modern password-hashing algorithm.
- Never store raw card details. Use an approved payment provider and its tokenized/hosted payment flow.
- Treat NID images, phone numbers, addresses, health-related service notes and media as sensitive data.
- Collect only the information required for the service; restrict access, encrypt data in transit and at rest, and define retention/deletion policies.
- Do not expose exact provider or customer locations unnecessarily. Share location only when needed for an active booking and with clear user awareness.
- Require explicit consent before capturing or publishing images/videos. Do not make public media evidence a default requirement.
- Enforce authorization on every protected backend operation; hiding a frontend button is not security.
- Maintain audit logs for important administrative, identity and financial actions.
- Add rate limits, abuse prevention, secure file upload validation, backups and tested restore procedures.
- Provide a way to report unsafe conduct, block another user, cancel where appropriate and reach human support.
Roadmap
Phase 1 — Discovery and foundation
- Interview customers and providers in a small target area
- Validate service categories, fee assumptions and operational workflows
- Define policies for identity checks, regulated services, cancellations, refunds and disputes
- Write user stories, acceptance criteria, data model and threat model
Phase 2 — MVP
- Authentication and profiles
- Configurable service categories and provider skills
- Service request creation and provider acceptance
- Booking lifecycle and completion confirmation
- Basic location capture and map handoff
- Cash payment recording, fee ledger and transaction history
- Ratings/reviews, admin tools, notifications and audit trail
Phase 3 — Controlled pilot
- Add approved digital payment integrations after provider onboarding and compliance review
- Improve matching, search, provider availability and customer support
- Monitor service quality, fraud, cancellations and safety reports
- Test backups, recovery, security and operational playbooks
Phase 4 — Scale when evidence supports it
- Redis caching, background queues and search improvements
- Observability, load testing, database tuning and read replicas if needed
- Separate services only where team ownership, deployment needs or measured bottlenecks justify it
- Consider Kafka for durable event streams and Kubernetes when operational scale warrants its complexity
### -Contributing

Contributions should include a clear problem statement, tests for behavior changes, documentation updates where appropriate, and no secrets or real customer data in commits. Use environment variables or a secret manager for credentials. Follow the repository's contribution and code-review rules as they are added.
### - Disclaimer

*Guniapa is a planned marketplace concept. Availability, identity checks, payments, maps, provider credentials, ratings, media uploads and other capabilities must be implemented, tested and reviewed before being represented as operational. The platform should launch only after legal, safety, privacy and payment requirements for its target markets have been reviewed.
>>>>>>> origin/main
