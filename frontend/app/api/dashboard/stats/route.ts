import { NextResponse } from "next/server";

const backendBase = (process.env.NEXT_PUBLIC_API_URL || "").trim().replace(/\/$/, "");
const backendUrl = backendBase ? `${backendBase}/api/v1/dashboard/stats` : "";
const sharedSecret = process.env.NEXT_PUBLIC_BACKEND_SECRET || "befs-super-secret-key-12345";

/**
 * Dashboard stats kommer alltid fra backend (én kilde til sannhet).
 */
export async function GET() {
    try {
        if (!backendUrl) {
            console.warn("[Stats API] NEXT_PUBLIC_API_URL ikke satt – returnerer null-tall");
            return NextResponse.json({
                properties: 0,
                contracts: 0,
                risks: 0,
                total_annual_rent: 0,
                total_maintenance_cost: 0,
                critical_deviations: 0,
                expiring_contracts: 0,
            });
        }

        const res = await fetch(backendUrl, {
            cache: "no-store",
            headers: {
                "Content-Type": "application/json",
                Authorization: `Bearer ${sharedSecret}`,
            },
        });

        if (!res.ok) {
            console.error("[Stats API] Backend error:", res.status, await res.text().catch(() => ""));
            return NextResponse.json({
                properties: 0,
                contracts: 0,
                risks: 0,
                total_annual_rent: 0,
                total_maintenance_cost: 0,
                critical_deviations: 0,
                expiring_contracts: 0,
            });
        }

        const data = await res.json();
        return NextResponse.json({
            properties: data.properties ?? 0,
            contracts: data.contracts ?? 0,
            leietakere: data.leietakere ?? 0,
            risks: data.risks ?? 0,
            total_annual_rent: data.total_annual_rent ?? 0,
            total_maintenance_cost: data.total_maintenance_cost ?? 0,
            critical_deviations: data.critical_deviations ?? 0,
            expiring_contracts: data.expiring_contracts ?? 0,
        });
    } catch (error: any) {
        console.error("[DashboardStats API Error]:", error);
        return NextResponse.json({
            properties: 0,
            contracts: 0,
            risks: 0,
            total_annual_rent: 0,
            total_maintenance_cost: 0,
            critical_deviations: 0,
            expiring_contracts: 0,
        });
    }
}
