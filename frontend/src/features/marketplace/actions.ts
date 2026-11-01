"use server";

import { revalidatePath } from "next/cache";
import { getSession, type UserRole } from "@/lib/session";
import { mutateBackend } from "@/lib/backend-api";

export type MarketplaceActionState = {
  error?: string;
  info?: string;
};

function value(formData: FormData, key: string): string {
  return String(formData.get(key) ?? "").trim();
}

export async function updateProviderAvailabilityAction(
  _previousState: MarketplaceActionState,
  formData: FormData,
): Promise<MarketplaceActionState> {
  const roleError = await checkRole("PROVIDER");
  if (roleError) return roleError;
  const availability = value(formData, "is_available");
  if (!["true", "false"].includes(availability)) {
    return { error: "Choose whether your profile should be available." };
  }
  const result = await mutateBackend<unknown>(
    "api/v1/providers/profile/",
    "PATCH",
    { is_available: availability === "true" },
  );
  if (!result.ok) return { error: result.error };
  revalidatePath("/dashboard/provider");
  return {
    info: availability === "true" ? "You are now available for requests." : "You are now unavailable for requests.",
  };
}

function validAmount(amount: string): boolean {
  return /^\d{1,8}(?:\.\d{1,2})?$/.test(amount) && Number(amount) > 0;
}

export async function cancelServiceRequestAction(
  _previousState: MarketplaceActionState,
  formData: FormData,
): Promise<MarketplaceActionState> {
  const roleError = await checkRole("CUSTOMER");
  if (roleError) return roleError;
  const requestId = value(formData, "request_id");
  if (!requestId) return { error: "This service request is unavailable." };
  const result = await mutateBackend<unknown>(
    `api/v1/requests/${encodeURIComponent(requestId)}/`,
    "DELETE",
  );
  if (!result.ok) return { error: result.error };
  revalidatePath("/dashboard/customer");
  return { info: "Your service request was cancelled." };
}

async function checkRole(
  expectedRole: UserRole,
): Promise<MarketplaceActionState | null> {
  const user = await getSession();
  if (!user) return { error: "Your session expired. Sign in again to continue." };
  if (user.role !== expectedRole) {
    return { error: "This action is not available for your account." };
  }
  return null;
}

async function postAction(
  path: string,
  body: unknown,
  success: string,
  route: string,
): Promise<MarketplaceActionState> {
  const result = await mutateBackend<unknown>(path, "POST", body);
  if (!result.ok) return { error: result.error };
  revalidatePath(route);
  return { info: success };
}

export async function createServiceRequestAction(
  _previousState: MarketplaceActionState,
  formData: FormData,
): Promise<MarketplaceActionState> {
  const roleError = await checkRole("CUSTOMER");
  if (roleError) return roleError;

  const category = value(formData, "category");
  const details = value(formData, "details");
  const serviceCity = value(formData, "service_city");
  const serviceAddress = value(formData, "service_address");
  const requestedFor = value(formData, "requested_for");
  const pricingModel = value(formData, "pricing_model");
  const proposedAmount = value(formData, "proposed_amount");
  const durationHours = value(formData, "duration_hours");

  if (!category || !details || !serviceCity || !serviceAddress || !requestedFor) {
    return { error: "Complete each required service request field." };
  }
  if (details.length > 2000 || serviceAddress.length > 500 || serviceCity.length > 100) {
    return { error: "Some request details exceed the allowed length." };
  }
  if (!["FIXED", "HOURLY", "QUOTE"].includes(pricingModel)) {
    return { error: "Choose an available pricing method." };
  }
  if (pricingModel !== "QUOTE" && !validAmount(proposedAmount)) {
    return { error: "Enter a valid service price or hourly rate." };
  }
  if (pricingModel === "QUOTE" && proposedAmount && !validAmount(proposedAmount)) {
    return { error: "Enter a valid optional budget." };
  }
  if (
    pricingModel === "HOURLY" &&
    (!/^\d{1,3}(?:\.\d{1,2})?$/.test(durationHours) ||
      Number(durationHours) <= 0)
  ) {
    return { error: "Enter the estimated service duration in hours." };
  }

  const requestedAt = new Date(`${requestedFor}+06:00`);
  if (Number.isNaN(requestedAt.valueOf()) || requestedAt <= new Date()) {
    return { error: "Choose a future service date and time." };
  }

  const body = {
    category,
    details,
    service_city: serviceCity,
    service_address: serviceAddress,
    requested_for: requestedAt.toISOString(),
    pricing_model: pricingModel,
    ...(proposedAmount ? { proposed_amount: proposedAmount } : {}),
    ...(pricingModel === "HOURLY" ? { duration_hours: durationHours } : {}),
  };
  return postAction(
    "api/v1/requests/",
    body,
    "Your service request was sent to eligible providers.",
    "/dashboard/customer",
  );
}

export async function createProviderProfileAction(
  _previousState: MarketplaceActionState,
  formData: FormData,
): Promise<MarketplaceActionState> {
  const roleError = await checkRole("PROVIDER");
  if (roleError) return roleError;
  const title = value(formData, "professional_title");
  const bio = value(formData, "bio");
  const city = value(formData, "city");
  const serviceArea = value(formData, "service_area");
  const experience = value(formData, "experience_years");
  const radius = value(formData, "service_radius_km");
  if (!title || !city || !serviceArea) {
    return { error: "Add a professional title, city, and service area." };
  }
  if (title.length > 150 || city.length > 100 || serviceArea.length > 255 || bio.length > 1000) {
    return { error: "Some profile details exceed the allowed length." };
  }
  if (!/^\d{1,2}$/.test(experience) || Number(experience) > 60) {
    return { error: "Enter experience between 0 and 60 years." };
  }
  if (!/^\d{1,3}$/.test(radius) || Number(radius) < 1 || Number(radius) > 100) {
    return { error: "Choose a service radius from 1 to 100 km." };
  }
  return postAction(
    "api/v1/providers/profile/",
    {
      professional_title: title,
      bio,
      experience_years: Number(experience),
      city,
      service_area: serviceArea,
      service_radius_km: Number(radius),
    },
    "Your provider profile was submitted for review.",
    "/dashboard/provider",
  );
}

export async function createProviderSkillAction(
  _previousState: MarketplaceActionState,
  formData: FormData,
): Promise<MarketplaceActionState> {
  const roleError = await checkRole("PROVIDER");
  if (roleError) return roleError;
  const category = value(formData, "category");
  const experience = value(formData, "experience_years");
  const description = value(formData, "description");
  if (
    !category ||
    !/^\d{1,2}$/.test(experience) ||
    Number(experience) > 60 ||
    description.length > 500
  ) {
    return { error: "Choose a category and enter valid experience years." };
  }
  return postAction(
    "api/v1/providers/skills/",
    {
      category,
      experience_years: Number(experience),
      description,
    },
    "Your skill was submitted for review.",
    "/dashboard/provider",
  );
}

export async function acceptServiceRequestAction(
  _previousState: MarketplaceActionState,
  formData: FormData,
): Promise<MarketplaceActionState> {
  const roleError = await checkRole("PROVIDER");
  if (roleError) return roleError;
  const requestId = value(formData, "request_id");
  if (!requestId) return { error: "This service request is unavailable." };
  return postAction(
    `api/v1/requests/${encodeURIComponent(requestId)}/accept/`,
    {},
    "You accepted the service request.",
    "/dashboard/provider",
  );
}

export async function submitServiceOfferAction(
  _previousState: MarketplaceActionState,
  formData: FormData,
): Promise<MarketplaceActionState> {
  const roleError = await checkRole("PROVIDER");
  if (roleError) return roleError;
  const requestId = value(formData, "request_id");
  const amount = value(formData, "amount");
  const message = value(formData, "message");
  if (!requestId || !validAmount(amount)) {
    return { error: "Enter a quote greater than zero." };
  }
  return postAction(
    `api/v1/requests/${encodeURIComponent(requestId)}/offers/`,
    { amount, message },
    "Your quote was sent to the customer.",
    "/dashboard/provider",
  );
}

export async function decideServiceOfferAction(
  _previousState: MarketplaceActionState,
  formData: FormData,
): Promise<MarketplaceActionState> {
  const roleError = await checkRole("CUSTOMER");
  if (roleError) return roleError;
  const offerId = value(formData, "offer_id");
  const decision = value(formData, "decision");
  if (!offerId || !["accept", "decline"].includes(decision)) {
    return { error: "Choose whether to accept or decline this quote." };
  }
  return postAction(
    `api/v1/offers/${encodeURIComponent(offerId)}/${decision}/`,
    {},
    decision === "accept" ? "You accepted the provider’s quote." : "You declined the quote.",
    "/dashboard/customer",
  );
}

export async function transitionBookingAction(
  _previousState: MarketplaceActionState,
  formData: FormData,
): Promise<MarketplaceActionState> {
  const user = await getSession();
  if (!user) return { error: "Your session expired. Sign in again to continue." };
  const bookingId = value(formData, "booking_id");
  const nextStatus = value(formData, "status");
  if (!bookingId || !nextStatus) return { error: "This booking action is unavailable." };
  const route =
    user.role === "PROVIDER" ? "/dashboard/provider" : "/dashboard/customer";
  return postAction(
    `api/v1/bookings/${encodeURIComponent(bookingId)}/transition/`,
    { status: nextStatus },
    "The booking status was updated.",
    route,
  );
}

export async function recordCashPaymentAction(
  _previousState: MarketplaceActionState,
  formData: FormData,
): Promise<MarketplaceActionState> {
  const roleError = await checkRole("PROVIDER");
  if (roleError) return roleError;
  const bookingId = value(formData, "booking_id");
  if (!bookingId) return { error: "This booking is unavailable." };
  return postAction(
    `api/v1/bookings/${encodeURIComponent(bookingId)}/cash-payment/`,
    {},
    "Cash payment was recorded.",
    "/dashboard/provider",
  );
}

export async function createReviewAction(
  _previousState: MarketplaceActionState,
  formData: FormData,
): Promise<MarketplaceActionState> {
  const roleError = await checkRole("CUSTOMER");
  if (roleError) return roleError;
  const bookingId = value(formData, "booking_id");
  const rating = value(formData, "rating");
  const comment = value(formData, "comment");
  if (!bookingId || !/^[1-5]$/.test(rating) || comment.length > 1000) {
    return { error: "Choose a rating from 1 to 5 and check your comment." };
  }
  return postAction(
    `api/v1/bookings/${encodeURIComponent(bookingId)}/reviews/`,
    { rating: Number(rating), comment },
    "Thank you. Your review was submitted for moderation.",
    "/dashboard/customer",
  );
}

export async function createSupportTicketAction(
  _previousState: MarketplaceActionState,
  formData: FormData,
): Promise<MarketplaceActionState> {
  const user = await getSession();
  if (!user) return { error: "Your session expired. Sign in again to continue." };
  const subject = value(formData, "subject");
  const description = value(formData, "description");
  const booking = value(formData, "booking");
  if (!subject || !description || subject.length > 160 || description.length > 3000) {
    return { error: "Add a subject and describe the issue in 3,000 characters or fewer." };
  }
  const route =
    user.role === "PROVIDER" ? "/dashboard/provider" : "/dashboard/customer";
  return postAction(
    "api/v1/support/tickets/",
    { subject, description, ...(booking ? { booking } : {}) },
    "Your support request was submitted.",
    route,
  );
}

export async function markNotificationReadAction(
  _previousState: MarketplaceActionState,
  formData: FormData,
): Promise<MarketplaceActionState> {
  const user = await getSession();
  if (!user) return { error: "Your session expired. Sign in again to continue." };
  const notificationId = value(formData, "notification_id");
  if (!notificationId) return { error: "This notification is unavailable." };
  const route =
    user.role === "PROVIDER" ? "/dashboard/provider" : "/dashboard/customer";
  return postAction(
    `api/v1/notifications/${encodeURIComponent(notificationId)}/read/`,
    {},
    "Notification marked as read.",
    route,
  );
}
