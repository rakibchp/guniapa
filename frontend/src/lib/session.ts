import "server-only";

import { createHmac, timingSafeEqual } from "node:crypto";
import { cookies } from "next/headers";

export const roles = ["CUSTOMER", "PROVIDER", "ADMIN"] as const;
export type UserRole = (typeof roles)[number];

export type SessionUser = {
  id: string;
  full_name: string;
  role: UserRole;
  is_phone_verified: boolean;
};

type SessionPayload = SessionUser & { expires_at: number };

export const sessionCookieNames = {
  access: "guniapa_access",
  refresh: "guniapa_refresh",
  user: "guniapa_user",
} as const;

function sessionSecret(): string {
  const secret = process.env.SESSION_SECRET;
  if (!secret || secret.length < 32) {
    throw new Error("SESSION_SECRET must be set to at least 32 characters.");
  }
  return secret;
}

function signature(value: string): Buffer {
  return createHmac("sha256", sessionSecret()).update(value).digest();
}

function isUserRole(value: unknown): value is UserRole {
  return typeof value === "string" && roles.includes(value as UserRole);
}

function isSessionPayload(value: unknown): value is SessionPayload {
  if (!value || typeof value !== "object") return false;
  const payload = value as Record<string, unknown>;
  return (
    typeof payload.id === "string" &&
    typeof payload.full_name === "string" &&
    isUserRole(payload.role) &&
    typeof payload.is_phone_verified === "boolean" &&
    typeof payload.expires_at === "number" &&
    payload.expires_at > Date.now()
  );
}

export function signSessionUser(
  user: SessionUser,
  expiresAt = Date.now() + 15 * 60 * 1000,
): string {
  const payload = Buffer.from(
    JSON.stringify({ ...user, expires_at: expiresAt }),
  ).toString("base64url");
  return `${payload}.${signature(payload).toString("base64url")}`;
}

export function verifySessionCookie(value: string): SessionUser | null {
  const [payload, encodedSignature, ...rest] = value.split(".");
  if (!payload || !encodedSignature || rest.length > 0) return null;

  const providedSignature = Buffer.from(encodedSignature, "base64url");
  const expectedSignature = signature(payload);
  if (
    providedSignature.length !== expectedSignature.length ||
    !timingSafeEqual(providedSignature, expectedSignature)
  ) {
    return null;
  }

  try {
    const parsed: unknown = JSON.parse(
      Buffer.from(payload, "base64url").toString("utf8"),
    );
    if (!isSessionPayload(parsed)) return null;
    return {
      id: parsed.id,
      full_name: parsed.full_name,
      role: parsed.role,
      is_phone_verified: parsed.is_phone_verified,
    };
  } catch {
    return null;
  }
}

const cookieOptions = {
  httpOnly: true,
  secure: process.env.NODE_ENV === "production",
  sameSite: "lax" as const,
  path: "/",
};

export async function saveSession(
  user: SessionUser,
  accessToken: string,
  refreshToken: string,
): Promise<void> {
  const signedUser = signSessionUser(user);
  const store = await cookies();
  store.set(sessionCookieNames.access, accessToken, {
    ...cookieOptions,
    maxAge: 15 * 60,
  });
  store.set(sessionCookieNames.refresh, refreshToken, {
    ...cookieOptions,
    maxAge: 7 * 24 * 60 * 60,
  });
  store.set(sessionCookieNames.user, signedUser, {
    ...cookieOptions,
    maxAge: 15 * 60,
  });
}

export async function getSession(): Promise<SessionUser | null> {
  const store = await cookies();
  const value = store.get(sessionCookieNames.user)?.value;
  return value ? verifySessionCookie(value) : null;
}

export async function clearSession(): Promise<void> {
  const store = await cookies();
  for (const name of Object.values(sessionCookieNames)) {
    store.set(name, "", { ...cookieOptions, maxAge: 0 });
  }
}

export async function getSessionTokens(): Promise<{
  access: string | undefined;
  refresh: string | undefined;
}> {
  const store = await cookies();
  return {
    access: store.get(sessionCookieNames.access)?.value,
    refresh: store.get(sessionCookieNames.refresh)?.value,
  };
}
