import { NextResponse } from "next/server";

const backendBase = (process.env.NEXT_PUBLIC_API_URL || "").trim().replace(/\/$/, "");
const sharedSecret = process.env.NEXT_PUBLIC_BACKEND_SECRET || "befs-super-secret-key-12345";

export async function GET(request: Request) {
    try {
        const { searchParams } = new URL(request.url);
        const year = searchParams.get("year") || "2026";

        if (!backendBase) {
            return NextResponse.json({ properties: [] });
        }

        const url = `${backendBase}/api/v1/risk/prioritized?year=${year}`;
        const res = await fetch(url, {
            cache: "no-store",
            headers: {
                "Content-Type": "application/json",
                Authorization: `Bearer ${sharedSecret}`,
            },
        });

        if (!res.ok) {
            console.error("[Risk Prioritized API] Backend error:", res.status, await res.text().catch(() => ""));
            return NextResponse.json({ properties: [] });
        }

        const data = await res.json();
        return NextResponse.json(data);
    } catch (error) {
        console.error("[Risk Prioritized API Error]:", error);
        return NextResponse.json({ properties: [] });
    }
}
