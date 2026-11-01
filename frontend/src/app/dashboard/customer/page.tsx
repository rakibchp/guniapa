import type { Metadata } from "next";
import { DashboardFrame } from "@/features/dashboard/dashboard-frame";
import {
  CancelRequestForm,
  MarkNotificationReadForm,
  ReviewForm,
  ServiceOfferActions,
  ServiceRequestForm,
  SupportTicketForm,
  BookingTransitionForm,
} from "@/features/marketplace/forms";
import {
  formatDate,
  formatMoney,
  readList,
  type Booking,
  type NotificationItem,
  type ServiceCategory,
  type ServiceOffer,
  type ServiceRequest,
  type SupportTicket,
} from "@/features/marketplace/data";

export const metadata: Metadata = { title: "Customer account" };

function DataError({ message }: { message: string }) {
  return <p className="dashboard-alert" role="alert">{message}</p>;
}

function EmptyState({ children }: { children: string }) {
  return <p className="dashboard-empty">{children}</p>;
}

export default async function CustomerDashboardPage() {
  const [categoriesResult, requestsResult, bookingsResult, ticketsResult, notificationsResult] =
    await Promise.all([
      readList<ServiceCategory>("api/v1/categories/"),
      readList<ServiceRequest>("api/v1/requests/"),
      readList<Booking>("api/v1/bookings/"),
      readList<SupportTicket>("api/v1/support/tickets/"),
      readList<NotificationItem>("api/v1/notifications/"),
    ]);

  const openRequests =
    requestsResult.ok
      ? requestsResult.data.filter(
          (request) =>
            request.status === "OPEN" && request.pricing_model === "QUOTE",
        )
      : [];
  const offerEntries = await Promise.all(
    openRequests.map(async (request) => [
      request.id,
      await readList<ServiceOffer>(
        `api/v1/requests/${encodeURIComponent(request.id)}/offers/`,
      ),
    ] as const),
  );
  const offersByRequest = new Map(offerEntries);
  const categoriesById = new Map(
    (categoriesResult.ok ? categoriesResult.data : []).map((category) => [
      category.id,
      category.name,
    ]),
  );

  return (
    <DashboardFrame role="CUSTOMER" title="Find the help you need">
      <section className="dashboard-section" aria-labelledby="create-request-title">
        <div className="dashboard-section-heading">
          <div>
            <p className="eyebrow">GET STARTED</p>
            <h2 id="create-request-title">Request a service</h2>
          </div>
        </div>
        {!categoriesResult.ok ? (
          <DataError message={categoriesResult.error} />
        ) : categoriesResult.data.length ? (
          <ServiceRequestForm categories={categoriesResult.data} />
        ) : (
          <EmptyState>Service categories are not available yet. Please check back soon.</EmptyState>
        )}
      </section>

      <section className="dashboard-section" aria-labelledby="requests-title">
        <div className="dashboard-section-heading">
          <div>
            <p className="eyebrow">YOUR ACTIVITY</p>
            <h2 id="requests-title">Service requests</h2>
          </div>
        </div>
        {!requestsResult.ok ? (
          <DataError message={requestsResult.error} />
        ) : requestsResult.data.length ? (
          <div className="dashboard-card-list">
            {requestsResult.data.map((request) => {
              const offersResult = offersByRequest.get(request.id);
              return (
                <article className="dashboard-card" key={request.id}>
                  <div className="dashboard-card-heading">
                    <div>
                      <p className="eyebrow">
                        {categoriesById.get(request.category) ?? "Service request"}
                      </p>
                      <h3>{request.service_city}</h3>
                    </div>
                    <span className="status-label">{request.status}</span>
                  </div>
                  <p>{request.details}</p>
                  <dl className="dashboard-facts">
                    <div>
                      <dt>When</dt>
                      <dd>{formatDate(request.requested_for)}</dd>
                    </div>
                    <div>
                      <dt>Pricing</dt>
                      <dd>
                        {request.pricing_model === "QUOTE"
                          ? "Quotes requested"
                          : request.pricing_model === "HOURLY"
                            ? `${formatMoney(request.proposed_amount, request.currency)} / hour`
                            : formatMoney(request.proposed_amount, request.currency)}
                      </dd>
                    </div>
                  </dl>
                  {request.status === "OPEN" &&
                    request.pricing_model === "QUOTE" && (
                      <div className="dashboard-subsection">
                        <h4>Provider quotes</h4>
                        {!offersResult ? (
                          <EmptyState>Quotes are not available for this request.</EmptyState>
                        ) : !offersResult.ok ? (
                          <DataError message={offersResult.error} />
                        ) : offersResult.data.length ? (
                          <div className="dashboard-card-list">
                            {offersResult.data.map((offer) => (
                              <div className="offer-row" key={offer.id}>
                                <div>
                                  <strong>{offer.provider_name}</strong>
                                  <span>{offer.professional_title} · {formatMoney(offer.amount)}</span>
                                  {offer.message && <p>{offer.message}</p>}
                                  <small>{offer.status}</small>
                                </div>
                                <ServiceOfferActions offer={offer} />
                              </div>
                            ))}
                          </div>
                        ) : (
                          <EmptyState>No quotes yet. Providers may still respond.</EmptyState>
                        )}
                      </div>
                    )}
                  {request.status === "OPEN" && (
                    <CancelRequestForm requestId={request.id} />
                  )}
                </article>
              );
            })}
          </div>
        ) : (
          <EmptyState>You have not requested a service yet.</EmptyState>
        )}
      </section>

      <section className="dashboard-section" aria-labelledby="bookings-title">
        <div className="dashboard-section-heading">
          <div>
            <p className="eyebrow">CONFIRMED WORK</p>
            <h2 id="bookings-title">Bookings</h2>
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
                    <h3>{booking.provider_name}</h3>
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
                <BookingTransitionForm booking={booking} role="CUSTOMER" />
                {booking.status === "COMPLETED" && (
                  <div className="dashboard-subsection">
                    <h4>Share your experience</h4>
                    <ReviewForm bookingId={booking.id} />
                  </div>
                )}
              </article>
            ))}
          </div>
        ) : (
          <EmptyState>Accepted requests will appear here as bookings.</EmptyState>
        )}
      </section>

      <section className="dashboard-section" aria-labelledby="notifications-title">
        <div className="dashboard-section-heading">
          <div>
            <p className="eyebrow">UPDATES</p>
            <h2 id="notifications-title">Notifications</h2>
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

      <section className="dashboard-section" aria-labelledby="support-title">
        <div className="dashboard-section-heading">
          <div>
            <p className="eyebrow">NEED HELP?</p>
            <h2 id="support-title">Support</h2>
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
