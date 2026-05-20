import { NextResponse } from "next/server";

const backendBase = (process.env.NEXT_PUBLIC_API_URL || "").trim().replace(/\/$/, "");
const sharedSecret = process.env.NEXT_PUBLIC_BACKEND_SECRET || "befs-super-secret-key-12345";

export async function GET() {
    try {
        const url = `${backendBase}/api/v1/dashboard/recent-activity`;
        const res = await fetch(url, {
            cache: "no-store",
            headers: { "Content-Type": "application/json", Authorization: `Bearer ${sharedSecret}` },
        });

        if (!res.ok) return NextResponse.json([], { status: 200 });
        return NextResponse.json(await res.json());
    } catch (error: any) {
        console.error("[RecentActivity API Error]:", error);
        return NextResponse.json([], { status: 200 });
    }
}
