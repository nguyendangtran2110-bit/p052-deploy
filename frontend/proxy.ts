import { NextResponse, type NextRequest } from "next/server";

export function buildContentSecurityPolicy(nonce: string, environment = process.env.NODE_ENV) {
  const development = environment === "development";
  const scriptDevelopmentPolicy = development ? " 'unsafe-eval'" : "";
  const stylePolicy = development ? "'self' 'unsafe-inline'" : `'self' 'nonce-${nonce}'`;
  const connectPolicy = development ? "'self' ws: wss:" : "'self'";
  const productionUpgradePolicy = development ? [] : ["upgrade-insecure-requests"];

  return [
    "default-src 'self'",
    `script-src 'self' 'nonce-${nonce}' 'strict-dynamic'${scriptDevelopmentPolicy}`,
    `style-src ${stylePolicy}`,
    "img-src 'self' data:",
    "font-src 'self'",
    `connect-src ${connectPolicy}`,
    "object-src 'none'",
    "base-uri 'self'",
    "form-action 'self'",
    "frame-ancestors 'none'",
    ...productionUpgradePolicy,
  ].join("; ");
}

export function proxy(request: NextRequest) {
  const nonce = Buffer.from(crypto.randomUUID()).toString("base64");
  const csp = buildContentSecurityPolicy(nonce);
  const requestHeaders = new Headers(request.headers);
  requestHeaders.set("x-nonce", nonce);
  requestHeaders.set("Content-Security-Policy", csp);
  const response = NextResponse.next({ request: { headers: requestHeaders } });
  response.headers.set("Content-Security-Policy", csp);
  if (request.nextUrl.pathname.startsWith("/manager/") || request.nextUrl.pathname.startsWith("/resident/")) {
    response.headers.set("Cache-Control", "no-store");
  }
  return response;
}

export const config = {
  matcher: [{ source: "/((?!api|_next/static|_next/image|favicon.ico).*)", missing: [{ type: "header", key: "next-router-prefetch" }] }],
};
