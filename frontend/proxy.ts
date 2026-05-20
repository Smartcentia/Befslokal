import { NextResponse } from "next/server";
import type { NextRequest } from "next/server";

// Next.js 16 proxy hook replacing middleware (pass-through)
export default function proxy(request: NextRequest) {
    return NextResponse.next();
}

export const config = {
    matcher: [
        "/((?!_next/static|_next/image|favicon.ico|.*\\.(?:svg|png|jpg|jpeg|gif|webp)$).*)",
    ],
};
