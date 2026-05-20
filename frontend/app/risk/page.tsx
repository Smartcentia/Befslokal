import {
    Table,
    TableBody,
    TableCell,
    TableHead,
    TableHeader,
    TableRow,
} from "@/components/ui/table"
import { Badge } from "@/components/ui/badge"
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card"
import { ExternalLink } from "lucide-react"
import Link from "next/link"
import { API_BASE_URL } from "@/lib/api/client"
import DataTooltip from "@/app/components/ui/DataTooltip"

interface PrioritizedProperty {
    property_id: string
    address: string
    name: string | null
    risk_score: number
    external_risk_score: number
    economic_risk_score: number
    risk_category: string
    annual_rent: number
    total_costs: number
    annual_cost: number
    priority_index: number
    reserve_factor: number
    budget_by_category: { property: number; operations: number; investment: number; other: number }
    open_deviations: number
}

interface PrioritizedResponse {
    properties: PrioritizedProperty[]
}

async function getPrioritizedProperties(year: number = 2026): Promise<PrioritizedProperty[]> {
    if (!API_BASE_URL) {
        return []
    }
    const apiUrl = `${API_BASE_URL}/risk/prioritized?year=${year}`

    const token = process.env.NEXT_PUBLIC_BACKEND_SECRET || "befs-super-secret-key-12345";

    try {
        const res = await fetch(apiUrl, {
            cache: "no-store",
            headers: {
                "Content-Type": "application/json",
                "Authorization": `Bearer ${token}`,
            },
        })

        if (!res.ok) {
            return []
        }

        const data = (await res.json()) as PrioritizedResponse
        return Array.isArray(data?.properties) ? data.properties : []
    } catch {
        return []
    }
}

function formatCurrency(n: number): string {
    if (n >= 1_000_000) return `${(n / 1_000_000).toFixed(1)}M`
    if (n >= 1_000) return `${(n / 1_000).toFixed(0)}k`
    return n.toLocaleString("no-NO", { maximumFractionDigits: 0 })
}

export default async function RiskDashboard() {
    const year = 2026
    const properties = await getPrioritizedProperties(year)

    const highRiskCount = properties.filter((p) => p.risk_score > 40).length
    const criticalCount = properties.filter((p) => p.risk_score > 75).length

    const totalBudget = (p: PrioritizedProperty) =>
        (p.budget_by_category?.property || 0) +
        (p.budget_by_category?.operations || 0) +
        (p.budget_by_category?.investment || 0) +
        (p.budget_by_category?.other || 0)

    return (
        <div className="space-y-6">
            <div>
                <h1 className="text-3xl font-bold tracking-tight">Risikobildet</h1>
                <p className="text-muted-foreground">
                    Oversikt over eiendommer sortert etter prioriteringsindeks. Prioritet = risikoscore × årskostnad. Brukes til å styre hvor midler prioriteres.
                </p>
            </div>

            <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4">
                <Card>
                    <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                        <CardTitle className="text-sm font-medium">Totalt på overvåking</CardTitle>
                    </CardHeader>
                    <CardContent>
                        <div className="text-2xl font-bold">{properties.length}</div>
                    </CardContent>
                </Card>
                <Card>
                    <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                        <CardTitle className="text-sm font-medium">Kritisk risiko</CardTitle>
                    </CardHeader>
                    <CardContent>
                        <div className="text-2xl font-bold text-destructive">{criticalCount}</div>
                    </CardContent>
                </Card>
                <Card>
                    <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                        <CardTitle className="text-sm font-medium">Høy risiko</CardTitle>
                    </CardHeader>
                    <CardContent>
                        <div className="text-2xl font-bold">{highRiskCount}</div>
                    </CardContent>
                </Card>
            </div>

            <Card>
                <CardHeader>
                    <CardTitle>Prioritert watchlist</CardTitle>
                    <CardDescription>
                        Eiendommer sortert etter prioriteringsindeks (risikoscore × årskostnad). Brukes til å styre hvor midler bør prioriteres.
                    </CardDescription>
                </CardHeader>
                <CardContent>
                    <Table>
                        <TableHeader>
                            <TableRow>
                                <TableHead>Eiendom</TableHead>
                                <TableHead>Score</TableHead>
                                <TableHead>
                                    <DataTooltip content="Ekstern risiko (flom, skred, etc.)">
                                        Ekstern
                                    </DataTooltip>
                                </TableHead>
                                <TableHead>
                                    <DataTooltip content="Økonomisk risiko (kostnad/leie, budsjettavvik)">
                                        Økonomisk
                                    </DataTooltip>
                                </TableHead>
                                <TableHead>Kategori</TableHead>
                                <TableHead className="text-right">Årskostnad</TableHead>
                                <TableHead className="text-right">Budsjett</TableHead>
                                <TableHead className="text-right">
                                    <DataTooltip content="Prioritet = risikoscore × årskostnad. Brukes til å styre hvor midler prioriteres.">
                                        Prioritet
                                    </DataTooltip>
                                </TableHead>
                                <TableHead className="text-right">Reservefaktor</TableHead>
                                <TableHead>Åpne avvik</TableHead>
                                <TableHead className="text-right">Handling</TableHead>
                            </TableRow>
                        </TableHeader>
                        <TableBody>
                            {properties.map((item) => (
                                <TableRow key={item.property_id}>
                                    <TableCell className="font-medium">{item.address || item.name || "-"}</TableCell>
                                    <TableCell>
                                        <span className="font-mono text-xs">
                                            {Number(item.risk_score ?? 0).toFixed(1)}
                                        </span>
                                    </TableCell>
                                    <TableCell>
                                        <span className={`font-mono text-xs ${item.external_risk_score > 50 ? 'text-destructive font-bold' : ''}`}>
                                            {item.external_risk_score?.toFixed(1) || "0.0"}
                                        </span>
                                    </TableCell>
                                    <TableCell>
                                        <span className={`font-mono text-xs ${item.economic_risk_score > 50 ? 'text-destructive font-bold' : ''}`}>
                                            {item.economic_risk_score?.toFixed(1) || "0.0"}
                                        </span>
                                    </TableCell>
                                    <TableCell>
                                        <Badge
                                            variant={
                                                item.risk_category?.toLowerCase() === "critical"
                                                    ? "destructive"
                                                    : item.risk_category?.toLowerCase() === "high"
                                                        ? "outline"
                                                        : "secondary"
                                            }
                                        >
                                            {item.risk_category || "moderat"}
                                        </Badge>
                                    </TableCell>
                                    <TableCell className="text-right font-mono text-sm">
                                        {formatCurrency(item.annual_cost)}
                                    </TableCell>
                                    <TableCell className="text-right font-mono text-sm">
                                        {formatCurrency(totalBudget(item))}
                                    </TableCell>
                                    <TableCell className="text-right font-mono text-sm">
                                        {formatCurrency(item.priority_index)}
                                    </TableCell>
                                    <TableCell className="text-right">{item.reserve_factor}</TableCell>
                                    <TableCell>{item.open_deviations}</TableCell>
                                    <TableCell className="text-right">
                                        <Link
                                            href={`/properties/${item.property_id}`}
                                            className="inline-flex items-center text-sm font-medium text-primary hover:underline"
                                        >
                                            Se detaljer <ExternalLink className="ml-1 h-3 w-3" />
                                        </Link>
                                    </TableCell>
                                </TableRow>
                            ))}
                        </TableBody>
                    </Table>
                </CardContent>
            </Card>
        </div>
    )
}
