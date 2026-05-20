import { NextResponse } from "next/server";

const backendBase = (process.env.NEXT_PUBLIC_API_URL || "").trim().replace(/\/$/, "");
const sharedSecret = process.env.NEXT_PUBLIC_BACKEND_SECRET || "befs-super-secret-key-12345";

export async function GET(request: Request) {
    try {
        const { searchParams } = new URL(request.url);
        const limit = searchParams.get("limit") || "50";
        const skip = searchParams.get("skip") || "0";
        const usage = searchParams.get("usage") || "";
        const search = searchParams.get("search") || "";

        const params = new URLSearchParams({ limit, skip });
        if (usage) params.append("usage", usage);
        if (search) params.append("search", search);

        const url = `${backendBase}/api/v1/properties?${params.toString()}`;
        const res = await fetch(url, {
            cache: "no-store",
            headers: { "Content-Type": "application/json", Authorization: `Bearer ${sharedSecret}` },
        });

        if (!res.ok) return NextResponse.json([], { status: res.status });
        return NextResponse.json(await res.json());
    } catch (error: any) {
        console.error("[Properties API Error]:", error);
        return NextResponse.json([], { status: 200 });
    }
}
