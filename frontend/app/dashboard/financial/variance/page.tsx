"use client"

export const dynamic = "force-dynamic"

import { useState, useEffect, Suspense } from "react"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { PeriodSelector } from "@/components/financial/PeriodSelector"
import { VarianceChart } from "@/components/financial/VarianceChart"
import { Loader2, Building2 } from "lucide-react"
import { useSearchParams, useRouter } from "next/navigation"
import { getProperties, Property } from "@/lib/api"
import { fetchAPI } from "@/lib/api/client"
import {
    Select,
    SelectContent,
    SelectItem,
    SelectTrigger,
    SelectValue,
} from "@/components/ui/select"

interface VarianceData {
    summary: {
        total_budget: number
        total_actual: number
        total_variance: number
        total_variance_pct: number
    }
    items: Array<{
        category: string
        budget: number
        actual: number
        variance: number
        variance_pct: number
    }>
}

function VarianceContent() {
    const searchParams = useSearchParams()
    const router = useRouter()
    const urlPropertyId = searchParams.get("propertyId")

    const [propertyId, setPropertyId] = useState<string | null>(urlPropertyId)
    const [properties, setProperties] = useState<Property[]>([])

    const [year, setYear] = useState(2025)
    const [periodType, setPeriodType] = useState<"month" | "quarter" | "ytd" | "year">("ytd")
    const [periodValue, setPeriodValue] = useState<number | null>(6)

    const [data, setData] = useState<VarianceData | null>(null)
    const [loading, setLoading] = useState(false)
    const [error, setError] = useState<string | null>(null)

    // Load Properties on mount
    useEffect(() => {
        async function loadProps() {
            try {
                const props = await getProperties()
                setProperties(props)
                // If ID in URL is "SELECT" (from menu), clear it
                if (urlPropertyId === "SELECT") {
                    setPropertyId(null)
                }
            } catch (e) {
                console.error("Failed to load properties", e)
            }
        }
        loadProps()
    }, [])

    // Sync local state with URL
    useEffect(() => {
        if (urlPropertyId && urlPropertyId !== "SELECT") {
            setPropertyId(urlPropertyId)
        }
    }, [urlPropertyId])

    useEffect(() => {
        if (!propertyId || propertyId === "SELECT") return
        fetchData()
    }, [propertyId, year, periodType, periodValue])

    const handlePropertyChange = (newId: string) => {
        setPropertyId(newId)
        router.push(`/dashboard/financial/variance?propertyId=${newId}`)
    }

    async function fetchData() {
        setLoading(true)
        setError(null)
        try {
            const params = new URLSearchParams({ year: String(year), period_type: periodType })
            if (periodValue != null) params.set("period_value", String(periodValue))
            const json = await fetchAPI<VarianceData>(
                `/variance/${propertyId}?${params.toString()}`
            )
            setData(json)
        } catch (err: unknown) {
            console.error(err)
            const msg = err instanceof Error ? err.message : String(err)
            // Prøv å hente ut detail fra API-svar (400/500)
            const detailMatch = msg.match(/"detail"\s*:\s*"([^"]+)"/)
            setError(
                detailMatch
                    ? detailMatch[1].replace(/\\"/g, '"')
                    : "Kunne ikke laste avviksdata. Sjekk at eiendommen har budsjettdata (kjør budsjettgenerering) og utgifter (manual_expenses)."
            )
        } finally {
            setLoading(false)
        }
    }

    return (
        <div className="space-y-6 max-w-7xl mx-auto p-6">
            <div className="flex flex-col xl:flex-row justify-between items-start xl:items-center gap-6">
                <div>
                    <div className="flex items-center gap-3 mb-2">
                        <Building2 className="h-8 w-8 text-primary" />
                        <h2 className="text-3xl font-bold tracking-tight">Avviksanalyse</h2>
                    </div>
                    <p className="text-muted-foreground">Analysere avvik mellom budsjett og regnskap.</p>
                </div>

                <div className="flex flex-col sm:flex-row gap-4 items-end">
                    {/* Property Selector */}
                    <div className="grid w-[280px] gap-1.5">
                        <Select
                            value={propertyId || ""}
                            onValueChange={handlePropertyChange}
                        >
                            <SelectTrigger className="h-10">
                                <SelectValue placeholder="Velg Eiendom" />
                            </SelectTrigger>
                            <SelectContent>
                                {properties.map((p) => (
                                    <SelectItem key={p.property_id} value={p.property_id}>
                                        {p.name}
                                    </SelectItem>
                                ))}
                            </SelectContent>
                        </Select>
                    </div>

                    <PeriodSelector
                        year={year} setYear={setYear}
                        periodType={periodType} setPeriodType={setPeriodType}
                        periodValue={periodValue} setPeriodValue={setPeriodValue}
                    />
                </div>
            </div>

            {!propertyId && (
                <div className="flex flex-col items-center justify-center py-20 border-2 border-dashed border-white/10 rounded-xl bg-white/5">
                    <Building2 className="h-12 w-12 text-muted-foreground mb-4" />
                    <h3 className="text-lg font-medium">Ingen eiendom valgt</h3>
                    <p className="text-sm text-muted-foreground mb-4">Velg en eiendom fra listen over for å se avvik.</p>
                </div>
            )}

            {loading && (
                <div className="flex justify-center p-12">
                    <Loader2 className="h-8 w-8 animate-spin text-muted-foreground" />
                </div>
            )}

            {error && (
                <div className="p-4 bg-destructive/10 text-destructive rounded-md">
                    {error}
                </div>
            )}

            {data && !loading && propertyId && (
                <>
                    {/* Summary Cards */}
                    <div className="grid gap-4 md:grid-cols-4">
                        <Card>
                            <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                                <CardTitle className="text-sm font-medium">Budsjett</CardTitle>
                            </CardHeader>
                            <CardContent>
                                <div className="text-2xl font-bold">
                                    {new Intl.NumberFormat("no-NO", { style: "currency", currency: "NOK", maximumFractionDigits: 0 }).format(data.summary.total_budget)}
                                </div>
                            </CardContent>
                        </Card>
                        <Card>
                            <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                                <CardTitle className="text-sm font-medium">Regnskap</CardTitle>
                            </CardHeader>
                            <CardContent>
                                <div className="text-2xl font-bold">
                                    {new Intl.NumberFormat("no-NO", { style: "currency", currency: "NOK", maximumFractionDigits: 0 }).format(data.summary.total_actual)}
                                </div>
                            </CardContent>
                        </Card>
                        <Card>
                            <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                                <CardTitle className="text-sm font-medium">Total Avvik</CardTitle>
                            </CardHeader>
                            <CardContent>
                                <div className={`text-2xl font-bold ${data.summary.total_variance < 0 ? 'text-destructive' : 'text-green-600'}`}>
                                    {new Intl.NumberFormat("no-NO", { style: "currency", currency: "NOK", maximumFractionDigits: 0 }).format(data.summary.total_variance)}
                                </div>
                                <p className="text-xs text-muted-foreground">
                                    {data.summary.total_variance_pct.toFixed(1)}% avvik
                                </p>
                            </CardContent>
                        </Card>
                        <Card>
                            <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                                <CardTitle className="text-sm font-medium">Status</CardTitle>
                            </CardHeader>
                            <CardContent>
                                <div className="text-2xl font-bold">
                                    {Math.abs(data.summary.total_variance_pct) < 5 ? "Akseptabelt" : "Krever Tiltak"}
                                </div>
                            </CardContent>
                        </Card>
                    </div>

                    <div className="grid gap-4 md:grid-cols-1 lg:grid-cols-2">
                        <Card className="col-span-2">
                            <CardHeader>
                                <CardTitle>Budsjett vs Regnskap per Kategori</CardTitle>
                            </CardHeader>
                            <CardContent className="pl-2">
                                <VarianceChart data={data.items} />
                            </CardContent>
                        </Card>
                    </div>

                    {/* Detailed Table */}
                    <Card>
                        <CardHeader>
                            <CardTitle>Detaljert Oversikt</CardTitle>
                        </CardHeader>
                        <CardContent>
                            <div className="relative w-full overflow-auto">
                                <table className="w-full caption-bottom text-sm text-left">
                                    <thead className="[&_tr]:border-b">
                                        <tr className="border-b transition-colors hover:bg-muted/50 data-[state=selected]:bg-muted">
                                            <th className="h-12 px-4 align-middle font-medium text-muted-foreground">Kategori</th>
                                            <th className="h-12 px-4 align-middle font-medium text-muted-foreground text-right">Budsjett</th>
                                            <th className="h-12 px-4 align-middle font-medium text-muted-foreground text-right">Regnskap</th>
                                            <th className="h-12 px-4 align-middle font-medium text-muted-foreground text-right">Avvik</th>
                                            <th className="h-12 px-4 align-middle font-medium text-muted-foreground text-right">%</th>
                                        </tr>
                                    </thead>
                                    <tbody className="[&_tr:last-child]:border-0">
                                        {data.items.map((item) => (
                                            <tr key={item.category} className="border-b transition-colors hover:bg-muted/50">
                                                <td className="p-4 align-middle font-medium">{item.category}</td>
                                                <td className="p-4 align-middle text-right">
                                                    {new Intl.NumberFormat("no-NO").format(Math.round(item.budget))}
                                                </td>
                                                <td className="p-4 align-middle text-right">
                                                    {new Intl.NumberFormat("no-NO").format(Math.round(item.actual))}
                                                </td>
                                                <td className={`p-4 align-middle text-right font-bold ${item.variance < 0 ? 'text-destructive' : 'text-green-600'}`}>
                                                    {new Intl.NumberFormat("no-NO").format(Math.round(item.variance))}
                                                </td>
                                                <td className="p-4 align-middle text-right">
                                                    {item.variance_pct.toFixed(1)}%
                                                </td>
                                            </tr>
                                        ))}
                                    </tbody>
                                </table>
                            </div>
                        </CardContent>
                    </Card>
                </>
            )}
        </div>
    )
}

export default function VariancePage() {
    return (
        <Suspense fallback={<div className="flex justify-center p-12"><Loader2 className="h-8 w-8 animate-spin" /></div>}>
            <VarianceContent />
        </Suspense>
    )
}
