// frontend/middleware.ts
// This file sits at the root of the frontend/ folder (next to app/)

import { NextResponse } from "next/server";
import type { NextRequest } from "next/server";

// Role → allowed route prefixes
const ROLE_ROUTES: Record<string, string[]> = {
  admin:   ["/admin",   "/finance", "/admission"],
  teacher: ["/teacher"],
  parent:  ["/parent"],
  student: ["/student"],
};

export function middleware(request: NextRequest) {
  const { pathname } = request.nextUrl;

  const isPublicRoute =
    pathname === "/" ||
    pathname === "/login" ||
    pathname === "/register" ||
    pathname === "/pricing";

  // Always allow public routes
  if (
    isPublicRoute ||
    pathname.startsWith("/_next") ||
    pathname.startsWith("/api") ||
    pathname.includes(".")
  ) {
    return NextResponse.next();
  }

  // Read auth from cookie (we'll set this on login)
  const authCookie = request.cookies.get("school-os-auth")?.value;

  if (!authCookie) {
    return NextResponse.redirect(new URL("/login", request.url));
  }

  try {
    const auth = JSON.parse(authCookie);
    const role: string = auth?.state?.user?.role;

    if (!role) {
      return NextResponse.redirect(new URL("/login", request.url));
    }

    const allowed = ROLE_ROUTES[role] ?? [];
    const hasAccess = allowed.some((prefix) => pathname.startsWith(prefix));

    if (!hasAccess) {
      // Redirect to their own dashboard
      const home = allowed[0] ?? "/login";
      return NextResponse.redirect(new URL(home, request.url));
    }
  } catch {
    return NextResponse.redirect(new URL("/login", request.url));
  }

  return NextResponse.next();
}

export const config = {
  matcher: [
    "/((?!_next/static|_next/image|favicon.ico).*)",
  ],
};
