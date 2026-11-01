# Guniapa frontend

Responsive Next.js, React, TypeScript and Tailwind CSS application. Customer and provider dashboards use server-rendered, authenticated calls to the Django API; forms submit through Next.js server actions.

## Local development

```sh
npm ci
cp .env.example .env.local
```

Set `SESSION_SECRET` to a private value of at least 32 characters. For example, generate one with `openssl rand -hex 32`. Never use the example value outside local development.

Start the Django API at `http://127.0.0.1:8000`, then run:

```sh
npm run dev
```

The app is available at `http://localhost:3000`. If the API uses another origin, update `GUNIAPA_API_BASE_URL`. In development, the OTP endpoint may return a `development_otp`; the verification page displays it only when the backend explicitly includes it.

## Authentication and authorization

- Registration, login, phone OTP send/verify, refresh and logout call Django from server actions or the request proxy.
- Access and refresh tokens are stored in `HttpOnly`, `SameSite=Lax` cookies, never browser `localStorage`; cookies are `Secure` in production.
- The proxy validates the user against `/api/v1/auth/me/`, refreshes expired access tokens and routes users to their role dashboard. The signed user cookie is only a server-rendering aid, not authorization.
- Marketplace mutations are server actions. Django remains authoritative for role and object permissions on every protected endpoint.
- Logout attempts to blacklist the refresh token. Local cookies are cleared even if the API cannot confirm revocation, and the UI reports that outcome.
- Set a private `SESSION_SECRET` and use HTTPS in production. Keep `GUNIAPA_API_BASE_URL` server-side; never expose tokens or private configuration in `NEXT_PUBLIC_*`.

## Connected workflows

| Workflow | Django API |
| --- | --- |
| Categories | `GET /api/v1/categories/` |
| Customer requests | `GET, POST /api/v1/requests/`; `DELETE /api/v1/requests/{id}/` |
| Customer quotes | `GET /api/v1/requests/{id}/offers/`; `POST /api/v1/offers/{id}/accept/` or `/decline/` |
| Provider onboarding | `GET, POST, PATCH /api/v1/providers/profile/`; `GET, POST /api/v1/providers/skills/` |
| Provider request feed | `GET /api/v1/requests/available/`; `POST /api/v1/requests/{id}/accept/` or `/offers/` |
| Bookings | `GET /api/v1/bookings/`; `POST /api/v1/bookings/{id}/transition/` |
| Cash receipt and reviews | `POST /api/v1/bookings/{id}/cash-payment/` and `/reviews/` |
| Support and updates | `GET, POST /api/v1/support/tickets/`; `GET /api/v1/notifications/`; `POST /api/v1/notifications/{id}/read/` |

Paginated API results are handled by the dashboards. Provider request cards do not expose a customer’s exact address; the address appears only on a booking. Customer address and schedule are explicitly shown as private booking details.

## Release limitations

- The backend has no live SMS provider. Production OTP delivery is unavailable until an adapter is implemented and configured.
- The administrator dashboard remains an account landing page; category, profile, skill, fee and moderation administration is through Django admin.
- Digital payments, maps, identity document processing, email verification, and regulated credential upload/review are not integrated.
- Seed at least one active category and configure policies/fees using an authorized administrator before pilot use. No real categories or fee defaults are fabricated.
- See the repository [deployment and operations guide](../DEPLOYMENT.md) for release gates and validation.

## Checks

```sh
npm run lint
npx tsc --noEmit
npm run build
```
