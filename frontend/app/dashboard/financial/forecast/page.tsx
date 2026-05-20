"use client"

export const dynamic = "force-dynamic"

import { useState, useEffect, Suspense } from "react"
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card"
import { ForecastChart } from "@/components/financial/ForecastChart"
import { Loader2, TrendingUp, SlidersHorizontal } from "lucide-react"
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
import { Slider } from "@/components/ui/slider"

interface ForecastData {
    property_id: string
    params: {
        inflation_rate: number
        horizon_months: number
        lookback_months: number
    }
    baseline_monthly_spend: number
    series: Array<{
        date: string
        amount: number
        type: "actual" | "forecast"
        lower_bound?: number
        upper_bound?: number
    }>
}

function ForecastContent() {
    const searchParams = useSearchParams()
    const router = useRouter()

    // State
    const [propertyId, setPropertyId] = useState<string | null>(null)
    const [properties, setProperties] = useState<Property[]>([])

    const [inflation, setInflation] = useState([3.5]) // Array for ShadCN Slider
    const [horizon, setHorizon] = useState(24) // Months

    const [data, setData] = useState<ForecastData | null>(null)
    const [loading, setLoading] = useState(false)
    const [error, setError] = useState<string | null>(null)

    // Load Properties
    useEffect(() => {
        async function loadProps() {
            try {
                const props = await getProperties()
                setProperties(props)

                // Check URL param?
                const urlId = searchParams.get("propertyId")
                if (urlId && urlId !== "SELECT") {
                    setPropertyId(urlId)
                }
            } catch (e) {
                console.error("Failed to load properties", e)
            }
        }
        loadProps()
    }, [searchParams])

    // Fetch Forecast
    useEffect(() => {
        if (!propertyId) return

        async function fetchForecast() {
            setLoading(true)
            setError(null)
            try {
                const inflationRate = inflation[0] / 100
                const params = new URLSearchParams({
                    months: String(horizon),
                    inflation: String(inflationRate),
                    lookback: "12",
                })
                const json = await fetchAPI<ForecastData>(
                    `/forecast/${propertyId}?${params.toString()}`
                )
                setData(json)
            } catch (err: unknown) {
                console.error(err)
                const msg = err instanceof Error ? err.message : String(err)
                const detailMatch = msg.match(/"detail"\s*:\s*"([^"]+)"/)
                setError(
                    detailMatch
                        ? detailMatch[1].replace(/\\"/g, '"')
                        : "Kunne ikke generere prognose. Mangler kanskje historiske data (utgifter eller financial_history)."
                )
            } finally {
                setLoading(false)
            }
        }

        // Debounce slightly?
        const timer = setTimeout(fetchForecast, 500)
        return () => clearTimeout(timer)

    }, [propertyId, inflation, horizon])

    const handlePropertyChange = (newId: string) => {
        setPropertyId(newId)
        router.push(`/dashboard/financial/forecast?propertyId=${newId}`)
    }

    return (
        <div className="space-y-6 max-w-7xl mx-auto p-6">
            <div className="flex flex-col xl:flex-row justify-between items-start xl:items-center gap-6">
                <div>
                    <div className="flex items-center gap-3 mb-2">
                        <TrendingUp className="h-8 w-8 text-primary" />
                        <h2 className="text-3xl font-bold tracking-tight">Rullerende Prognoser</h2>
                    </div>
                    <p className="text-muted-foreground">Prosjektere fremtidige kostnader basert på historisk regnskap.</p>
                </div>

                {/* Property Selector */}
                <div className="grid w-70 gap-1.5">
                    <Select
                        value={propertyId || ""}
                        onValueChange={handlePropertyChange}
                    >
                        <SelectTrigger className="h-10">
                            <SelectValue placeholder="Velg Eiendom" />
                        </SelectTrigger>
                        <SelectContent>
                            {properties.map((p) => (
                                <SelectItem key={p.property_id} value={p.property_id || ""}>
                                    {p.name}
                                </SelectItem>
                            ))}
                        </SelectContent>
                    </Select>
                </div>
            </div>

            {!propertyId && (
                <div className="flex flex-col items-center justify-center py-20 border-2 border-dashed border-white/10 rounded-xl bg-white/5">
                    <TrendingUp className="h-12 w-12 text-muted-foreground mb-4" />
                    <h3 className="text-lg font-medium">Ingen eiendom valgt</h3>
                    <p className="text-sm text-muted-foreground mb-4">Velg en eiendom for å se fremtidige kostnadsprognoser.</p>
                </div>
            )}

            {propertyId && (
                <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
                    {/* Controls */}
                    <Card className="lg:col-span-1 h-fit">
                        <CardHeader>
                            <CardTitle className="flex items-center gap-2">
                                <SlidersHorizontal size={20} />
                                Parametere
                            </CardTitle>
                            <CardDescription>Justér forutsetningene for prognosen</CardDescription>
                        </CardHeader>
                        <CardContent className="space-y-8">
                            <div className="space-y-4">
                                <div className="flex justify-between">
                                    <label className="text-sm font-medium">Inflasjonsjustering (årlig)</label>
                                    <span className="text-sm font-bold text-primary">{inflation[0]}%</span>
                                </div>
                                <Slider
                                    value={inflation}
                                    onValueChange={setInflation}
                                    max={10}
                                    step={0.1}
                                    className="cursor-pointer"
                                />
                                <p className="text-xs text-muted-foreground">
                                    Simulerer kostnadsøkning (KPI) over tid.
                                </p>
                            </div>

                            <div className="space-y-4">
                                <div className="flex justify-between">
                                    <label className="text-sm font-medium">Prognosehorisont</label>
                                    <span className="text-sm font-bold">{horizon} md.</span>
                                </div>
                                <div className="flex gap-2">
                                    {[12, 24, 36, 60].map(m => (
                                        <button
                                            key={m}
                                            onClick={() => setHorizon(m)}
                                            className={`px-3 py-1 text-xs rounded-full border transition-colors ${horizon === m
                                                ? "bg-primary text-white border-primary"
                                                : "bg-transparent border-white/20 hover:bg-white/10"
                                                }`}
                                        >
                                            {m} mnd
                                        </button>
                                    ))}
                                </div>
                            </div>

                            {data && (
                                <div className="pt-4 border-t border-white/10">
                                    <h4 className="text-sm font-medium mb-2">Nøkkeltall</h4>
                                    <div className="flex justify-between text-sm">
                                        <span className="text-muted-foreground">Historisk snitt:</span>
                                        <span className="font-mono">
                                            {new Intl.NumberFormat("no-NO", { style: "currency", currency: "NOK", maximumFractionDigits: 0 }).format(data.baseline_monthly_spend)} / mnd
                                        </span>
                                    </div>
                                </div>
                            )}
                        </CardContent>
                    </Card>

                    {/* Chart */}
                    <Card className="lg:col-span-2 min-h-125">
                        <CardHeader>
                            <CardTitle>Kostnadsutvikling</CardTitle>
                            <CardDescription>
                                Historiske transaksjoner og fremtidig prognose
                            </CardDescription>
                        </CardHeader>
                        <CardContent>
                            {loading ? (
                                <div className="flex justify-center items-center h-100">
                                    <Loader2 className="h-8 w-8 animate-spin text-muted-foreground" />
                                </div>
                            ) : error ? (
                                <div className="flex flex-col items-center justify-center h-100 text-destructive gap-2">
                                    <p>{error}</p>
                                </div>
                            ) : data ? (
                                <ForecastChart data={data.series} />
                            ) : null}
                        </CardContent>
                    </Card>
                </div>
            )}
        </div>
    )
}

export default function ForecastPage() {
    return (
        <Suspense fallback={<div className="flex justify-center p-12"><Loader2 className="h-8 w-8 animate-spin" /></div>}>
            <ForecastContent />
        </Suspense>
    )
}
