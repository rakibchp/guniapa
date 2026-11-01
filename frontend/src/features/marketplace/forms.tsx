"use client";

import { useActionState } from "react";
import {
  acceptServiceRequestAction,
  cancelServiceRequestAction,
  createProviderProfileAction,
  createProviderSkillAction,
  createReviewAction,
  createServiceRequestAction,
  createSupportTicketAction,
  decideServiceOfferAction,
  markNotificationReadAction,
  recordCashPaymentAction,
  submitServiceOfferAction,
  transitionBookingAction,
  updateProviderAvailabilityAction,
  type MarketplaceActionState,
} from "@/features/marketplace/actions";
import type {
  Booking,
  NotificationItem,
  ServiceCategory,
  ServiceOffer,
  ServiceRequest,
} from "@/features/marketplace/data";

function Feedback({ state }: { state: MarketplaceActionState }) {
  if (!state.error && !state.info) return null;
  return (
    <p
      className={state.error ? "form-feedback form-feedback-error" : "form-feedback"}
      role={state.error ? "alert" : "status"}
      aria-live="polite"
    >
      {state.error ?? state.info}
    </p>
  );
}

function SubmitButton({
  pending,
  children,
}: {
  pending: boolean;
  children: string;
}) {
  return (
    <button className="button button-dark button-small" type="submit" disabled={pending}>
      {pending ? "Please wait…" : children}
    </button>
  );
}

export function ServiceRequestForm({
  categories,
}: {
  categories: ServiceCategory[];
}) {
  const [state, action, pending] = useActionState(createServiceRequestAction, {});
  return (
    <form className="market-form" action={action}>
      <div className="form-grid">
        <label>
          Service category
          <select name="category" required defaultValue="">
            <option value="" disabled>Select a service</option>
            {categories.map((category) => (
              <option key={category.id} value={category.id}>{category.name}</option>
            ))}
          </select>
        </label>
        <label>
          Pricing
          <select name="pricing_model" required defaultValue="FIXED">
            <option value="FIXED">Fixed price</option>
            <option value="HOURLY">Hourly rate</option>
            <option value="QUOTE">Request quotes</option>
          </select>
        </label>
        <label>
          City
          <input name="service_city" required maxLength={100} autoComplete="address-level2" />
        </label>
        <label>
          Service address
          <input name="service_address" required maxLength={500} autoComplete="street-address" />
        </label>
        <label>
          Date and time (Bangladesh time)
          <input name="requested_for" type="datetime-local" required />
        </label>
        <label>
          Budget or price (BDT)
          <input name="proposed_amount" inputMode="decimal" placeholder="Optional for quotes" />
        </label>
        <label className="form-grid-wide">
          What do you need done?
          <textarea name="details" required maxLength={2000} rows={4} />
        </label>
        <label>
          Estimated hours (hourly only)
          <input name="duration_hours" inputMode="decimal" placeholder="e.g. 2" />
        </label>
      </div>
      <p className="form-hint">
        Your address is shared with the assigned provider after a booking is accepted.
      </p>
      <Feedback state={state} />
      <SubmitButton pending={pending}>Post service request</SubmitButton>
    </form>
  );
}

export function ProviderProfileForm() {
  const [state, action, pending] = useActionState(createProviderProfileAction, {});
  return (
    <form className="market-form" action={action}>
      <div className="form-grid">
        <label>
          Professional title
          <input name="professional_title" required maxLength={120} />
        </label>
        <label>
          City
          <input name="city" required maxLength={100} />
        </label>
        <label>
          Service area
          <input name="service_area" required maxLength={200} />
        </label>
        <label>
          Service radius (km)
          <input name="service_radius_km" type="number" min={1} max={100} defaultValue={10} required />
        </label>
        <label>
          Years of experience
          <input name="experience_years" type="number" min={0} max={60} defaultValue={0} required />
        </label>
        <label className="form-grid-wide">
          Short professional bio
          <textarea name="bio" maxLength={2000} rows={4} />
        </label>
      </div>
      <p className="form-hint">Profiles are reviewed before they can receive service requests.</p>
      <Feedback state={state} />
      <SubmitButton pending={pending}>Submit provider profile</SubmitButton>
    </form>
  );
}

export function ProviderSkillForm({
  categories,
}: {
  categories: ServiceCategory[];
}) {
  const [state, action, pending] = useActionState(createProviderSkillAction, {});
  return (
    <form className="market-form compact-form" action={action}>
      <div className="form-grid">
        <label>
          Service category
          <select name="category" required defaultValue="">
            <option value="" disabled>Select a service</option>
            {categories.map((category) => (
              <option key={category.id} value={category.id}>{category.name}</option>
            ))}
          </select>
        </label>
        <label>
          Years of experience
          <input name="experience_years" type="number" min={0} max={60} defaultValue={0} required />
        </label>
        <label className="form-grid-wide">
          Relevant experience
          <textarea name="description" maxLength={500} rows={3} />
        </label>
      </div>
      <Feedback state={state} />
      <SubmitButton pending={pending}>Add skill</SubmitButton>
    </form>
  );
}

export function ProviderAvailabilityForm({ available }: { available: boolean }) {
  const [state, action, pending] = useActionState(updateProviderAvailabilityAction, {});
  return (
    <form className="inline-action-form" action={action}>
      <label>
        Availability
        <select name="is_available" defaultValue={String(available)}>
          <option value="true">Available</option>
          <option value="false">Unavailable</option>
        </select>
      </label>
      <SubmitButton pending={pending}>Save availability</SubmitButton>
      <Feedback state={state} />
    </form>
  );
}

export function ServiceRequestActions({
  request,
}: {
  request: ServiceRequest;
}) {
  const [acceptState, acceptAction, acceptPending] = useActionState(
    acceptServiceRequestAction,
    {},
  );
  const [offerState, offerAction, offerPending] = useActionState(
    submitServiceOfferAction,
    {},
  );
  return (
    <div className="card-actions">
      {request.pricing_model === "QUOTE" ? (
        <form className="inline-action-form" action={offerAction}>
          <input type="hidden" name="request_id" value={request.id} />
          <label>
            Your quote (BDT)
            <input name="amount" inputMode="decimal" required />
          </label>
          <label>
            Message
            <input name="message" maxLength={500} />
          </label>
          <SubmitButton pending={offerPending}>Send quote</SubmitButton>
          <Feedback state={offerState} />
        </form>
      ) : (
        <form className="inline-action-form" action={acceptAction}>
          <input type="hidden" name="request_id" value={request.id} />
          <Feedback state={acceptState} />
          <SubmitButton pending={acceptPending}>Accept request</SubmitButton>
        </form>
      )}
    </div>
  );
}

export function ServiceOfferActions({ offer }: { offer: ServiceOffer }) {
  const [state, action, pending] = useActionState(decideServiceOfferAction, {});
  if (offer.status !== "PENDING") return null;
  return (
    <form className="inline-action-form" action={action}>
      <input type="hidden" name="offer_id" value={offer.id} />
      <Feedback state={state} />
      <button
        className="button button-dark button-small"
        type="submit"
        name="decision"
        value="accept"
        disabled={pending}
      >
        Accept quote
      </button>
      <button
        className="button button-outline button-small"
        type="submit"
        name="decision"
        value="decline"
        disabled={pending}
      >
        Decline
      </button>
    </form>
  );
}

export function CancelRequestForm({ requestId }: { requestId: string }) {
  const [state, action, pending] = useActionState(cancelServiceRequestAction, {});
  return (
    <form className="inline-action-form" action={action}>
      <input type="hidden" name="request_id" value={requestId} />
      <Feedback state={state} />
      <button className="button button-outline button-small" type="submit" disabled={pending}>
        {pending ? "Please wait…" : "Cancel request"}
      </button>
    </form>
  );
}

const providerTransitions: Record<string, string[]> = {
  ACCEPTED: ["ARRIVING", "CANCELLED"],
  ARRIVING: ["IN_PROGRESS", "CANCELLED", "DISPUTED"],
  IN_PROGRESS: ["COMPLETION_PENDING", "DISPUTED"],
};

const customerTransitions: Record<string, string[]> = {
  ACCEPTED: ["CANCELLED"],
  ARRIVING: ["CANCELLED"],
  COMPLETION_PENDING: ["COMPLETED", "DISPUTED"],
};

const transitionLabels: Record<string, string> = {
  ARRIVING: "Mark as arriving",
  IN_PROGRESS: "Start service",
  COMPLETION_PENDING: "Mark work complete",
  COMPLETED: "Confirm completion",
  CANCELLED: "Cancel booking",
  DISPUTED: "Raise a dispute",
};

export function BookingTransitionForm({
  booking,
  role,
}: {
  booking: Booking;
  role: "CUSTOMER" | "PROVIDER";
}) {
  const [state, action, pending] = useActionState(transitionBookingAction, {});
  const transitions =
    role === "PROVIDER" ? providerTransitions : customerTransitions;
  const statuses = transitions[booking.status] ?? [];
  if (!statuses.length) return null;
  return (
    <form className="inline-action-form" action={action}>
      <input type="hidden" name="booking_id" value={booking.id} />
      <Feedback state={state} />
      {statuses.map((status) => (
        <button
          className={status === "CANCELLED" || status === "DISPUTED"
            ? "button button-outline button-small"
            : "button button-dark button-small"}
          key={status}
          type="submit"
          name="status"
          value={status}
          disabled={pending}
        >
          {pending ? "Please wait…" : transitionLabels[status]}
        </button>
      ))}
    </form>
  );
}

export function CashPaymentForm({ bookingId }: { bookingId: string }) {
  const [state, action, pending] = useActionState(recordCashPaymentAction, {});
  return (
    <form className="inline-action-form" action={action}>
      <input type="hidden" name="booking_id" value={bookingId} />
      <p className="form-hint">This records provider-reported cash; it is not an online payment.</p>
      <Feedback state={state} />
      <SubmitButton pending={pending}>Record cash received</SubmitButton>
    </form>
  );
}

export function ReviewForm({ bookingId }: { bookingId: string }) {
  const [state, action, pending] = useActionState(createReviewAction, {});
  return (
    <form className="market-form compact-form" action={action}>
      <input type="hidden" name="booking_id" value={bookingId} />
      <div className="form-grid">
        <label>
          Rating
          <select name="rating" defaultValue="5">
            {[5, 4, 3, 2, 1].map((rating) => (
              <option key={rating} value={rating}>{rating} / 5</option>
            ))}
          </select>
        </label>
        <label className="form-grid-wide">
          Review
          <textarea name="comment" maxLength={1000} rows={3} />
        </label>
      </div>
      <p className="form-hint">Reviews are moderated before being published.</p>
      <Feedback state={state} />
      <SubmitButton pending={pending}>Submit review</SubmitButton>
    </form>
  );
}

export function SupportTicketForm({ bookingId }: { bookingId?: string }) {
  const [state, action, pending] = useActionState(createSupportTicketAction, {});
  return (
    <form className="market-form compact-form" action={action}>
      {bookingId && <input type="hidden" name="booking" value={bookingId} />}
      <div className="form-grid">
        <label>
          Subject
          <input name="subject" required maxLength={160} />
        </label>
        <label className="form-grid-wide">
          How can we help?
          <textarea name="description" required maxLength={3000} rows={4} />
        </label>
      </div>
      <Feedback state={state} />
      <SubmitButton pending={pending}>Contact support</SubmitButton>
    </form>
  );
}

export function MarkNotificationReadForm({
  notification,
}: {
  notification: NotificationItem;
}) {
  const [state, action, pending] = useActionState(markNotificationReadAction, {});
  if (notification.is_read) return <span className="status-label">Read</span>;
  return (
    <form action={action}>
      <input type="hidden" name="notification_id" value={notification.id} />
      <button className="text-button" type="submit" disabled={pending}>
        {pending ? "Saving…" : "Mark read"}
      </button>
      <Feedback state={state} />
    </form>
  );
}
