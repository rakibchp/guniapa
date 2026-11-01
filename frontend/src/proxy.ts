import { NextResponse, type NextRequest } from "next/server";
import {
  roles,
  sessionCookieNames,
  signSessionUser,
  type SessionUser,
  type UserRole,
} from "@/lib/session";

type ApiResponse = {
  status: number;
  data: unknown;
};

class AccountServiceUnavailable extends Error {}

const roleRoutes: Record<UserRole, string> = {
  CUSTOMER: "/dashboard/customer",
  PROVIDER: "/dashboard/provider",
  ADMIN: "/dashboard/admin",
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

async function callApi(
  path: string,
  options: { accessToken?: string; body?: unknown } = {},
): Promise<ApiResponse> {
  let response: Response;
  try {
    response = await fetch(apiUrl(path), {
      method: options.body === undefined ? "GET" : "POST",
      headers: {
        ...(options.body === undefined
          ? {}
          : { "Content-Type": "application/json" }),
        ...(options.accessToken
          ? { Authorization: `Bearer ${options.accessToken}` }
          : {}),
      },
      ...(options.body === undefined
        ? {}
        : { body: JSON.stringify(options.body) }),
      cache: "no-store",
    });
  } catch (error) {
    if (error instanceof TypeError) {
      throw new AccountServiceUnavailable();
    }
    throw error;
  }

  let data: unknown = null;
  if (response.status !== 204) {
    try {
      data = await response.json();
    } catch (error) {
      if (error instanceof SyntaxError) {
        throw new AccountServiceUnavailable();
      }
      throw error;
    }
  }
  return { status: response.status, data };
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
    roles.includes(value.role as UserRole) &&
    value.is_phone_verified === true
  );
}

function clearSession(response: NextResponse): void {
  for (const name of Object.values(sessionCookieNames)) {
    response.cookies.set(name, "", { ...cookieOptions, maxAge: 0 });
  }
}

function expiredSession(request: NextRequest): NextResponse {
  const response = NextResponse.redirect(
    new URL("/login?expired=1", request.url),
  );
  clearSession(response);
  return response;
}

function unavailable(): NextResponse {
  return new NextResponse(
    "Account services are temporarily unavailable. Please try again.",
    {
      status: 503,
      headers: { "Content-Type": "text/plain; charset=utf-8" },
    },
  );
}

function saveUpdatedCookies(
  response: NextResponse,
  user: SessionUser,
  accessToken?: string,
  refreshToken?: string,
): void {
  if (accessToken) {
    response.cookies.set(sessionCookieNames.access, accessToken, {
      ...cookieOptions,
      maxAge: 15 * 60,
    });
  }
  if (refreshToken) {
    response.cookies.set(sessionCookieNames.refresh, refreshToken, {
      ...cookieOptions,
      maxAge: 7 * 24 * 60 * 60,
    });
  }
  response.cookies.set(
    sessionCookieNames.user,
    signSessionUser(user),
    {
      ...cookieOptions,
      maxAge: 15 * 60,
    },
  );
}

export async function proxy(request: NextRequest): Promise<NextResponse> {
  const accessToken = request.cookies.get(sessionCookieNames.access)?.value;
  const refreshToken = request.cookies.get(sessionCookieNames.refresh)?.value;
  if (!accessToken && !refreshToken) return expiredSession(request);

  try {
    let activeAccessToken = accessToken;
    let rotatedRefreshToken: string | undefined;
    let currentUserResponse: ApiResponse | null = null;

    if (activeAccessToken) {
      currentUserResponse = await callApi("api/v1/auth/me/", {
        accessToken: activeAccessToken,
      });
    }

    if (!currentUserResponse || currentUserResponse.status === 401) {
      if (!refreshToken) return expiredSession(request);
      const refreshed = await callApi("api/v1/auth/refresh/", {
        body: { refresh: refreshToken },
      });
      if (refreshed.status === 401 || refreshed.status === 400) {
        return expiredSession(request);
      }
      if (
        refreshed.status < 200 ||
        refreshed.status >= 300 ||
        !isRecord(refreshed.data) ||
        typeof refreshed.data.access !== "string"
      ) {
        return unavailable();
      }
      activeAccessToken = refreshed.data.access;
      rotatedRefreshToken =
        typeof refreshed.data.refresh === "string"
          ? refreshed.data.refresh
          : undefined;
      currentUserResponse = await callApi("api/v1/auth/me/", {
        accessToken: activeAccessToken,
      });
    }

    if (
      !currentUserResponse ||
      currentUserResponse.status === 401 ||
      currentUserResponse.status === 403
    ) {
      return expiredSession(request);
    }
    if (
      currentUserResponse.status < 200 ||
      currentUserResponse.status >= 300 ||
      !isSessionUser(currentUserResponse.data)
    ) {
      return unavailable();
    }

    const user = currentUserResponse.data;
    const destination = roleRoutes[user.role];
    const pathname = request.nextUrl.pathname;
    const response =
      pathname !== destination
        ? NextResponse.redirect(new URL(destination, request.url))
        : NextResponse.next();
    saveUpdatedCookies(response, user, activeAccessToken, rotatedRefreshToken);
    return response;
  } catch (error) {
    if (error instanceof AccountServiceUnavailable) return unavailable();
    throw error;
  }
}

export const config = {
  matcher: ["/dashboard/:path*"],
};
