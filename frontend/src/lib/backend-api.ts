import "server-only";

import { cookies } from "next/headers";
import {
  sessionCookieNames,
  signSessionUser,
  verifySessionCookie,
  type SessionUser,
} from "@/lib/session";

export type BackendResult<T> =
  | { ok: true; status: number; data: T }
  | { ok: false; status: number; error: string };

type JsonResponse = {
  status: number;
  data: unknown;
};

const cookieOptions = {
  httpOnly: true,
  secure: process.env.NODE_ENV === "production",
  sameSite: "lax" as const,
  path: "/",
};

function apiUrl(path: string): URL {
  const configuredBase =
    process.env.GUNIAPA_API_BASE_URL ?? "http://127.0.0.1:8000";
  const base = configuredBase.endsWith("/")
    ? configuredBase
    : `${configuredBase}/`;
  const url = new URL(path, base);
  if (
    (url.protocol !== "http:" && url.protocol !== "https:") ||
    url.username ||
    url.password
  ) {
    throw new Error("GUNIAPA_API_BASE_URL must be a valid HTTP(S) URL.");
  }
  return url;
}

function errorMessage(data: unknown, fallback: string): string {
  if (!data || typeof data !== "object") return fallback;
  const record = data as Record<string, unknown>;
  if (typeof record.message === "string") return record.message;
  if (typeof record.detail === "string") return record.detail;
  const errors = record.errors ?? record;
  if (typeof errors === "string") return errors;
  if (errors && typeof errors === "object") {
    const messages = Object.values(errors)
      .flatMap((value) => (Array.isArray(value) ? value : [value]))
      .filter((value): value is string => typeof value === "string");
    if (messages.length) return messages.join(" ");
  }
  return fallback;
}

async function fetchJSON(
  path: string,
  accessToken: string | undefined,
  method: "GET" | "POST" | "PATCH" | "DELETE",
  body?: unknown,
): Promise<JsonResponse> {
  let response: Response;
  try {
    response = await fetch(apiUrl(path), {
      method,
      headers: {
        ...(body === undefined ? {} : { "Content-Type": "application/json" }),
        ...(accessToken ? { Authorization: `Bearer ${accessToken}` } : {}),
      },
      ...(body === undefined ? {} : { body: JSON.stringify(body) }),
      cache: "no-store",
    });
  } catch (error) {
    if (error instanceof TypeError) {
      return {
        status: 503,
        data: { message: "We couldn't reach the account service." },
      };
    }
    throw error;
  }

  if (response.status === 204) return { status: 204, data: null };
  try {
    return { status: response.status, data: await response.json() };
  } catch (error) {
    if (error instanceof SyntaxError) {
      return {
        status: response.status,
        data: { message: "The account service returned an unreadable response." },
      };
    }
    throw error;
  }
}

export async function readBackend<T>(path: string): Promise<BackendResult<T>> {
  const store = await cookies();
  const response = await fetchJSON(
    path,
    store.get(sessionCookieNames.access)?.value,
    "GET",
  );
  if (response.status < 200 || response.status >= 300) {
    return {
      ok: false,
      status: response.status,
      error: errorMessage(response.data, "We couldn't load this information."),
    };
  }
  return { ok: true, status: response.status, data: response.data as T };
}

export async function mutateBackend<T>(
  path: string,
  method: "POST" | "PATCH" | "DELETE",
  body?: unknown,
): Promise<BackendResult<T>> {
  const store = await cookies();
  let accessToken = store.get(sessionCookieNames.access)?.value;
  let response = await fetchJSON(path, accessToken, method, body);

  if (response.status === 401) {
    const refreshToken = store.get(sessionCookieNames.refresh)?.value;
    if (!refreshToken) {
      return {
        ok: false,
        status: 401,
        error: "Your session expired. Sign in again to continue.",
      };
    }
    const refreshResponse = await fetchJSON(
      "api/v1/auth/refresh/",
      undefined,
      "POST",
      { refresh: refreshToken },
    );
    if (
      refreshResponse.status < 200 ||
      refreshResponse.status >= 300 ||
      !refreshResponse.data ||
      typeof refreshResponse.data !== "object"
    ) {
      return {
        ok: false,
        status: refreshResponse.status,
        error: "Your session expired. Sign in again to continue.",
      };
    }
    const tokenData = refreshResponse.data as Record<string, unknown>;
    if (typeof tokenData.access !== "string") {
      return {
        ok: false,
        status: 502,
        error: "The account service returned an incomplete session response.",
      };
    }
    accessToken = tokenData.access;
    store.set(sessionCookieNames.access, accessToken, {
      ...cookieOptions,
      maxAge: 15 * 60,
    });
    if (typeof tokenData.refresh === "string") {
      store.set(sessionCookieNames.refresh, tokenData.refresh, {
        ...cookieOptions,
        maxAge: 7 * 24 * 60 * 60,
      });
    }
    const currentUser = store.get(sessionCookieNames.user)?.value;
    const sessionUser: SessionUser | null = currentUser
      ? verifySessionCookie(currentUser)
      : null;
    if (sessionUser) {
      store.set(
        sessionCookieNames.user,
        signSessionUser(sessionUser),
        { ...cookieOptions, maxAge: 15 * 60 },
      );
    }
    response = await fetchJSON(path, accessToken, method, body);
  }

  if (response.status < 200 || response.status >= 300) {
    return {
      ok: false,
      status: response.status,
      error: errorMessage(response.data, "We couldn't complete that action."),
    };
  }
  return { ok: true, status: response.status, data: response.data as T };
}
