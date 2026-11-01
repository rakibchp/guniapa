import type { Metadata } from "next";
import { DashboardFrame } from "@/features/dashboard/dashboard-frame";
import {
  BookingTransitionForm,
  CashPaymentForm,
  MarkNotificationReadForm,
  ProviderAvailabilityForm,
  ProviderProfileForm,
  ProviderSkillForm,
  ServiceRequestActions,
  SupportTicketForm,
} from "@/features/marketplace/forms";
import {
  formatDate,
  formatMoney,
  readList,
  readProviderProfile,
  type Booking,
  type NotificationItem,
  type ProviderSkill,
  type ServiceCategory,
  type ServiceRequest,
  type SupportTicket,
} from "@/features/marketplace/data";

export const metadata: Metadata = { title: "Provider account" };

function DataError({ message }: { message: string }) {
  return <p className="dashboard-alert" role="alert">{message}</p>;
}

function EmptyState({ children }: { children: string }) {
  return <p className="dashboard-empty">{children}</p>;
}

const profileStatusText: Record<string, string> = {
  PENDING: "Your profile is awaiting review. You can add skills while you wait.",
  REJECTED: "Your profile was not approved. Contact support if you need help.",
  SUSPENDED: "Your profile is currently suspended. Contact support for assistance.",
  APPROVED: "Your profile is approved. Add approved skills and set your availability to receive requests.",
};

export default async function ProviderDashboardPage() {
  const [profileResult, categoriesResult, bookingsResult, ticketsResult, notificationsResult] =
    await Promise.all([
      readProviderProfile(),
      readList<ServiceCategory>("api/v1/categories/"),
      readList<Booking>("api/v1/bookings/"),
      readList<SupportTicket>("api/v1/support/tickets/"),
      readList<NotificationItem>("api/v1/notifications/"),
    ]);

  const profile = profileResult.ok ? profileResult.data : null;
  const [skillsResult, requestsResult] =
    profile && profileResult.ok
      ? await Promise.all([
          readList<ProviderSkill>("api/v1/providers/skills/"),
          profile.approval_status === "APPROVED" && profile.is_available
            ? readList<ServiceRequest>("api/v1/requests/available/")
            : Promise.resolve(null),
        ])
      : [null, null];
  const skillCategoryIds = new Set(
    skillsResult?.ok ? skillsResult.data.map((skill) => skill.category) : [],
  );
  const categoriesForSkillForm =
    categoriesResult.ok
      ? categoriesResult.data.filter((category) => !skillCategoryIds.has(category.id))
      : [];

  return (
    <DashboardFrame role="PROVIDER" title="Grow your service business">
      <section className="dashboard-section" aria-labelledby="profile-title">
        <div className="dashboard-section-heading">
          <div>
            <p className="eyebrow">PROVIDER ONBOARDING</p>
            <h2 id="profile-title">Your provider profile</h2>
          </div>
        </div>
        {!profileResult.ok ? (
          <DataError message={profileResult.error} />
        ) : profile ? (
          <div className="dashboard-card">
            <div className="dashboard-card-heading">
              <div>
                <p className="eyebrow">{profile.city} · {profile.service_radius_km} km radius</p>
                <h3>{profile.professional_title}</h3>
              </div>
              <span className="status-label">{profile.approval_status}</span>
            </div>
            <p>{profile.bio || profile.service_area}</p>
            <p className="form-hint">{profileStatusText[profile.approval_status]}</p>
            {profile.approval_status === "APPROVED" && (
              <ProviderAvailabilityForm available={profile.is_available} />
            )}
          </div>
        ) : (
          <div>
            <p className="form-hint">
              Create a provider profile to start onboarding. It must be reviewed before you can receive requests.
            </p>
            <ProviderProfileForm />
          </div>
        )}
      </section>

      {profile && profileResult.ok && (
        <section className="dashboard-section" aria-labelledby="skills-title">
          <div className="dashboard-section-heading">
            <div>
              <p className="eyebrow">YOUR SERVICES</p>
              <h2 id="skills-title">Skills and categories</h2>
            </div>
          </div>
          {!skillsResult ? (
            <EmptyState>Skills are available after your provider profile is created.</EmptyState>
          ) : !skillsResult.ok ? (
            <DataError message={skillsResult.error} />
          ) : skillsResult.data.length ? (
            <ul className="dashboard-list">
              {skillsResult.data.map((skill) => (
                <li key={skill.id}>
                  <div>
                    <strong>{skill.category_name}</strong>
                    <p>{skill.experience_years} years of experience{skill.description ? ` · ${skill.description}` : ""}</p>
                    <small>
                      {skill.approval_status}
                      {skill.credential_verified ? " · Credential verified" : ""}
                    </small>
                  </div>
                </li>
              ))}
            </ul>
          ) : (
            <EmptyState>You have not added any service skills yet.</EmptyState>
          )}
          {categoriesResult.ok ? (
            categoriesForSkillForm.length ? (
              <ProviderSkillForm categories={categoriesForSkillForm} />
            ) : (
              <p className="form-hint">No additional service categories are available.</p>
            )
          ) : (
            <DataError message={categoriesResult.error} />
          )}
        </section>
      )}

      {profile?.approval_status === "APPROVED" && profile.is_available && (
        <section className="dashboard-section" aria-labelledby="available-title">
          <div className="dashboard-section-heading">
            <div>
              <p className="eyebrow">MATCHED TO YOUR APPROVED SKILLS</p>
              <h2 id="available-title">Available service requests</h2>
            </div>
          </div>
          {!requestsResult ? (
            <EmptyState>Available requests will appear when your profile is approved and available.</EmptyState>
          ) : !requestsResult.ok ? (
            <DataError message={requestsResult.error} />
          ) : requestsResult.data.length ? (
            <div className="dashboard-card-list">
              {requestsResult.data.map((request) => (
                <article className="dashboard-card" key={request.id}>
                  <div className="dashboard-card-heading">
                    <div>
                      <p className="eyebrow">{request.category_name}</p>
                      <h3>{request.service_city}</h3>
                    </div>
                    <span className="status-label">{request.pricing_model}</span>
                  </div>
                  <p>{request.details}</p>
                  <dl className="dashboard-facts">
                    <div>
                      <dt>Requested for</dt>
                      <dd>{formatDate(request.requested_for)}</dd>
                    </div>
                    <div>
                      <dt>Customer budget</dt>
                      <dd>
                        {request.pricing_model === "HOURLY"
                          ? `${formatMoney(request.proposed_amount, request.currency)} / hour`
                          : formatMoney(request.proposed_amount, request.currency)}
                      </dd>
                    </div>
                    {request.duration_hours && (
                      <div>
                        <dt>Estimated hours</dt>
                        <dd>{request.duration_hours}</dd>
                      </div>
                    )}
                  </dl>
                  <p className="form-hint">
                    The exact service address is shared only after a booking is accepted.
                  </p>
                  <ServiceRequestActions request={request} />
                </article>
              ))}
            </div>
          ) : (
            <EmptyState>No matching service requests are available right now.</EmptyState>
          )}
        </section>
      )}

      <section className="dashboard-section" aria-labelledby="provider-bookings-title">
        <div className="dashboard-section-heading">
          <div>
            <p className="eyebrow">YOUR COMMITMENTS</p>
            <h2 id="provider-bookings-title">Bookings</h2>
          </div>
        </div>
        {!bookingsResult.ok ? (
          <DataError message={bookingsResult.error} />
        ) : bookingsResult.data.length ? (
          <div className="dashboard-card-list">
            {bookingsResult.data.map((booking) => (
              <article className="dashboard-card" key={booking.id}>
                <div className="dashboard-card-heading">
                  <div>
                    <p className="eyebrow">{booking.category_name}</p>
                    <h3>{booking.customer_name}</h3>
                  </div>
                  <span className="status-label">{booking.status.replaceAll("_", " ")}</span>
                </div>
                <p>{booking.details}</p>
                <dl className="dashboard-facts">
                  <div>
                    <dt>Service time</dt>
                    <dd>{formatDate(booking.requested_for)}</dd>
                  </div>
                  <div>
                    <dt>Agreed amount</dt>
                    <dd>{formatMoney(booking.agreed_amount, booking.currency)}</dd>
                  </div>
                  <div>
                    <dt>Service location</dt>
                    <dd>{booking.service_address}, {booking.service_city}</dd>
                  </div>
                </dl>
                <BookingTransitionForm booking={booking} role="PROVIDER" />
                {booking.status === "COMPLETED" && (
                  <CashPaymentForm bookingId={booking.id} />
                )}
              </article>
            ))}
          </div>
        ) : (
          <EmptyState>Accepted requests and quotes will appear here.</EmptyState>
        )}
      </section>

      <section className="dashboard-section" aria-labelledby="provider-updates-title">
        <div className="dashboard-section-heading">
          <div>
            <p className="eyebrow">UPDATES</p>
            <h2 id="provider-updates-title">Notifications</h2>
          </div>
        </div>
        {!notificationsResult.ok ? (
          <DataError message={notificationsResult.error} />
        ) : notificationsResult.data.length ? (
          <ul className="dashboard-list">
            {notificationsResult.data.map((notification) => (
              <li key={notification.id}>
                <div>
                  <p>{notification.message}</p>
                  <small>{formatDate(notification.created_at)}</small>
                </div>
                <MarkNotificationReadForm notification={notification} />
              </li>
            ))}
          </ul>
        ) : (
          <EmptyState>No notifications yet.</EmptyState>
        )}
      </section>

      <section className="dashboard-section" aria-labelledby="provider-support-title">
        <div className="dashboard-section-heading">
          <div>
            <p className="eyebrow">NEED HELP?</p>
            <h2 id="provider-support-title">Support</h2>
          </div>
        </div>
        <SupportTicketForm />
        {!ticketsResult.ok ? (
          <DataError message={ticketsResult.error} />
        ) : ticketsResult.data.length ? (
          <ul className="dashboard-list">
            {ticketsResult.data.map((ticket) => (
              <li key={ticket.id}>
                <div>
                  <strong>{ticket.subject}</strong>
                  <p>{ticket.description}</p>
                  <small>{ticket.status} · {formatDate(ticket.created_at)}</small>
                </div>
              </li>
            ))}
          </ul>
        ) : (
          <EmptyState>You have no support requests.</EmptyState>
        )}
      </section>
    </DashboardFrame>
  );
}
