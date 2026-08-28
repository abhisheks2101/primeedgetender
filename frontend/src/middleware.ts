import { NextResponse, type NextRequest } from "next/server";

import { getServerApiBaseUrl } from "@/lib/utils";

export async function middleware(request: NextRequest) {
  if (!request.nextUrl.pathname.startsWith("/app") && !request.nextUrl.pathname.startsWith("/admin")) {
    return NextResponse.next();
  }

  const cookie = request.headers.get("cookie") ?? "";
  const apiUrl = getServerApiBaseUrl();

  try {
    const response = await fetch(`${apiUrl}/api/auth/me`, {
      headers: {
        cookie,
        Accept: "application/json",
      },
      cache: "no-store",
    });

    if (response.ok) {
      return NextResponse.next();
    }
  } catch {
    // Fall through to redirect when backend is unavailable.
  }

  return NextResponse.redirect(new URL("/login", request.url));
}

export const config = {
  matcher: ["/app/:path*", "/admin/:path*"],
};
