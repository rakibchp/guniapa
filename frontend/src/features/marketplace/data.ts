import { readBackend, type BackendResult } from "@/lib/backend-api";

export type ServiceCategory = {
  id: string;
  name: string;
  description: string;
  requires_credential: boolean;
};

export type ServiceRequest = {
  id: string;
  category: string;
  category_name?: string;
  details: string;
  service_city: string;
  service_address?: string;
  requested_for: string;
  pricing_model: "FIXED" | "HOURLY" | "QUOTE";
  proposed_amount: string | null;
  duration_hours: string | null;
  currency: string;
  status: string;
  created_at: string;
};

export type ServiceOffer = {
  id: string;
  provider_id: string;
  provider_name: string;
  professional_title: string;
  amount: string;
  message: string;
  status: "PENDING" | "ACCEPTED" | "DECLINED" | "REVOKED";
  created_at: string;
};

export type Booking = {
  id: string;
  request_id: string;
  category_name: string;
  customer_name: string;
  provider_name: string;
  details: string;
  service_city: string;
  service_address: string;
  requested_for: string;
  pricing_model: string;
  proposed_amount: string | null;
  duration_hours: string | null;
  agreed_amount: string;
  customer_fee: string;
  provider_fee: string;
  currency: string;
  status: string;
  created_at: string;
  completed_at: string | null;
};

export type ProviderProfile = {
  id: string;
  professional_title: string;
  bio: string;
  experience_years: number;
  city: string;
  service_area: string;
  service_radius_km: number;
  approval_status: "PENDING" | "APPROVED" | "REJECTED" | "SUSPENDED";
  is_available: boolean;
};

export type ProviderSkill = {
  id: string;
  category: string;
  category_name: string;
  experience_years: number;
  description: string;
  approval_status: "PENDING" | "APPROVED" | "REJECTED";
  credential_verified: boolean;
};

export type SupportTicket = {
  id: string;
  booking: string | null;
  subject: string;
  description: string;
  status: string;
  created_at: string;
};

export type NotificationItem = {
  id: string;
  kind: string;
  message: string;
  booking: string | null;
  service_request: string | null;
  is_read: boolean;
  created_at: string;
};

function isRecord(value: unknown): value is Record<string, unknown> {
  return typeof value === "object" && value !== null;
}

function isProviderProfile(value: unknown): value is ProviderProfile {
  return (
    isRecord(value) &&
    typeof value.id === "string" &&
    typeof value.professional_title === "string" &&
    typeof value.bio === "string" &&
    typeof value.experience_years === "number" &&
    typeof value.city === "string" &&
    typeof value.service_area === "string" &&
    typeof value.service_radius_km === "number" &&
    ["PENDING", "APPROVED", "REJECTED", "SUSPENDED"].includes(
      String(value.approval_status),
    ) &&
    typeof value.is_available === "boolean"
  );
}

export async function readList<T>(
  path: string,
): Promise<BackendResult<T[]>> {
  const result = await readBackend<unknown>(path);
  if (!result.ok) return result;
  if (Array.isArray(result.data)) {
    return { ok: true, status: result.status, data: result.data as T[] };
  }
  if (
    isRecord(result.data) &&
    Array.isArray(result.data.results)
  ) {
    return {
      ok: true,
      status: result.status,
      data: result.data.results as T[],
    };
  }
  return {
    ok: false,
    status: 502,
    error: "The service returned a response in an unexpected format.",
  };
}

export async function readProviderProfile(): Promise<
  BackendResult<ProviderProfile | null>
> {
  const result = await readBackend<unknown>("api/v1/providers/profile/");
  if (!result.ok) {
    if (result.status === 404) {
      return { ok: true, status: 404, data: null };
    }
    return result;
  }
  if (!isRecord(result.data)) {
    return {
      ok: false,
      status: 502,
      error: "The service returned a provider profile in an unexpected format.",
    };
  }
  const profile =
    isRecord(result.data.data) ? result.data.data : result.data;
  if (!isProviderProfile(profile)) {
    return {
      ok: false,
      status: 502,
      error: "The service returned a provider profile in an unexpected format.",
    };
  }
  return {
    ok: true,
    status: result.status,
    data: profile,
  };
}

export function formatDate(value: string): string {
  const date = new Date(value);
  if (Number.isNaN(date.valueOf())) return "Date unavailable";
  return new Intl.DateTimeFormat("en-BD", {
    timeZone: "Asia/Dhaka",
    dateStyle: "medium",
    timeStyle: "short",
  }).format(date);
}

export function formatMoney(amount: string | null, currency = "BDT"): string {
  if (!amount || !Number.isFinite(Number(amount))) return "Quote requested";
  return new Intl.NumberFormat("en-BD", {
    style: "currency",
    currency,
    maximumFractionDigits: 2,
  }).format(Number(amount));
}
