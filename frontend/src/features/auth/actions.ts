"use server";

import { redirect } from "next/navigation";
import {
  clearSession,
  getSessionTokens,
  saveSession,
  type SessionUser,
  type UserRole,
} from "@/lib/session";

export type AuthActionState = {
  error?: string;
  info?: string;
};

const phonePattern = /^\+?[1-9]\d{7,14}$/;
const allowedRoles: UserRole[] = ["CUSTOMER", "PROVIDER"];

type ApiResult = {
  ok: boolean;
  data: unknown;
  message: string;
};

function getApiUrl(path: string): URL {
  const configuredBase =
    process.env.GUNIAPA_API_BASE_URL ?? "http://127.0.0.1:8000";
  const base = configuredBase.endsWith("/")
    ? configuredBase
    : `${configuredBase}/`;
  const url = new URL(path, base);
  if (url.protocol !== "http:" && url.protocol !== "https:") {
    throw new Error("GUNIAPA_API_BASE_URL must use HTTP or HTTPS.");
  }
  return url;
}

function errorText(value: unknown): string[] {
  if (typeof value === "string") return [value];
  if (Array.isArray(value)) return value.flatMap(errorText);
  if (value && typeof value === "object") {
    return Object.values(value).flatMap(errorText);
  }
  return [];
}

function getApiMessage(data: unknown, fallback: string): string {
  if (data && typeof data === "object") {
    const body = data as Record<string, unknown>;
    if (typeof body.message === "string") return body.message;
    const details = errorText(body.errors ?? body);
    if (details.length) return details.join(" ");
  }
  return fallback;
}

async function postApi(
  path: string,
  body: unknown,
  accessToken?: string,
): Promise<ApiResult> {
  let url: URL;
  try {
    url = getApiUrl(path);
  } catch (error) {
    return {
      ok: false,
      data: null,
      message:
        error instanceof Error
          ? error.message
          : "GUNIAPA_API_BASE_URL is not a valid URL.",
    };
  }

  let response: Response;
  try {
    response = await fetch(url, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        ...(accessToken ? { Authorization: `Bearer ${accessToken}` } : {}),
      },
      body: JSON.stringify(body),
      cache: "no-store",
    });
  } catch {
    return {
      ok: false,
      data: null,
      message: "We couldn't reach the account service. Please try again.",
    };
  }

  let data: unknown;
  try {
    data = await response.json();
  } catch {
    return {
      ok: false,
      data: null,
      message: "The account service returned an unreadable response.",
    };
  }

  return {
    ok: response.ok,
    data,
    message: response.ok
      ? ""
      : getApiMessage(data, "We couldn't complete that request."),
  };
}

function isRecord(value: unknown): value is Record<string, unknown> {
  return typeof value === "object" && value !== null;
}

function isSessionUser(value: unknown): value is SessionUser {
  return (
    isRecord(value) &&
    typeof value.id === "string" &&
    typeof value.full_name === "string" &&
    typeof value.role === "string" &&
    allowedRoles.concat("ADMIN").includes(value.role as UserRole) &&
    typeof value.is_phone_verified === "boolean"
  );
}

export async function loginAction(
  _previousState: AuthActionState,
  formData: FormData,
): Promise<AuthActionState> {
  const identifier = String(formData.get("identifier") ?? "").trim();
  const password = String(formData.get("password") ?? "");
  if (!identifier || !password) {
    return { error: "Enter your email or phone number and password." };
  }

  const result = await postApi("api/v1/auth/login/", { identifier, password });
  if (!result.ok) {
    return { error: result.message };
  }

  if (!isRecord(result.data)) {
    return { error: "The account service returned an invalid sign-in response." };
  }
  const tokens = result.data.tokens;
  if (
    !isRecord(tokens) ||
    typeof tokens.access !== "string" ||
    typeof tokens.refresh !== "string" ||
    !isSessionUser(result.data.user)
  ) {
    return { error: "The account service returned an incomplete sign-in response." };
  }
  if (!result.data.user.is_phone_verified) {
    return { error: "Verify your phone number before signing in." };
  }

  try {
    await saveSession(result.data.user, tokens.access, tokens.refresh);
  } catch (error) {
    return {
      error:
        error instanceof Error
          ? error.message
          : "We couldn't create a secure session.",
    };
  }

  redirect("/dashboard");
}

export async function registerAction(
  _previousState: AuthActionState,
  formData: FormData,
): Promise<AuthActionState> {
  const fullName = String(formData.get("full_name") ?? "").trim();
  const email = String(formData.get("email") ?? "").trim();
  const phoneNumber = String(formData.get("phone_number") ?? "").trim();
  const password = String(formData.get("password") ?? "");
  const role = String(formData.get("role") ?? "");

  if (!fullName || !email || !phoneNumber || !password) {
    return { error: "Complete every field to create your account." };
  }
  if (fullName.length > 150) {
    return { error: "Your name must be 150 characters or fewer." };
  }
  if (!phonePattern.test(phoneNumber)) {
    return { error: "Enter your phone number in international format, such as +8801XXXXXXXXX." };
  }
  if (!allowedRoles.includes(role as UserRole)) {
    return { error: "Choose whether you're joining as a customer or provider." };
  }
  if (password.length < 8) {
    return { error: "Use a password with at least 8 characters." };
  }

  const result = await postApi("api/v1/auth/register/", {
    full_name: fullName,
    email,
    phone_number: phoneNumber,
    password,
    role,
  });
  if (!result.ok) return { error: result.message };

  redirect("/verify-phone");
}

export async function sendOtpAction(
  _previousState: AuthActionState,
  formData: FormData,
): Promise<AuthActionState> {
  const phoneNumber = String(formData.get("phone_number") ?? "").trim();
  if (!phonePattern.test(phoneNumber)) {
    return { error: "Enter the phone number used when you registered." };
  }

  const result = await postApi("api/v1/auth/otp/send/", {
    phone_number: phoneNumber,
  });
  if (!result.ok) return { error: result.message };

  const developmentOtp =
    isRecord(result.data) && typeof result.data.development_otp === "string"
      ? result.data.development_otp
      : null;
  return {
    info: developmentOtp
      ? `Development OTP: ${developmentOtp}`
      : "If this number can be verified, a code has been sent.",
  };
}

export async function verifyOtpAction(
  _previousState: AuthActionState,
  formData: FormData,
): Promise<AuthActionState> {
  const phoneNumber = String(formData.get("phone_number") ?? "").trim();
  const otp = String(formData.get("otp") ?? "").trim();
  if (!phonePattern.test(phoneNumber)) {
    return { error: "Enter the phone number used when you registered." };
  }
  if (!/^\d{6}$/.test(otp)) {
    return { error: "Enter the 6-digit code." };
  }

  const result = await postApi("api/v1/auth/otp/verify/", {
    phone_number: phoneNumber,
    otp,
  });
  if (!result.ok) return { error: result.message };

  redirect("/login?verified=1");
}

export async function signOutAction(): Promise<void> {
  const tokens = await getSessionTokens();
  await clearSession();

  if (!tokens.access || !tokens.refresh) {
    redirect("/login?logout=unconfirmed");
  }

  const result = await postApi("api/v1/auth/logout/", {
    refresh: tokens.refresh,
  }, tokens.access);
  redirect(result.ok ? "/login?logout=done" : "/login?logout=unconfirmed");
}
