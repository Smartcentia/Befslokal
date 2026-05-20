"use client"

import {
    BarChart,
    Bar,
    XAxis,
    YAxis,
    CartesianGrid,
    Tooltip,
    Legend,
    ResponsiveContainer,
    ReferenceLine,
} from "recharts"

interface VarianceItem {
    category: string
    budget: number
    actual: number
    variance: number
    variance_pct: number
}

interface VarianceChartProps {
    data: VarianceItem[]
}

export function VarianceChart({ data }: VarianceChartProps) {
    return (
        <div className="h-[400px] w-full">
            <ResponsiveContainer width="100%" height="100%">
                <BarChart
                    data={data}
                    margin={{
                        top: 20,
                        right: 30,
                        left: 20,
                        bottom: 5,
                    }}
                >
                    <CartesianGrid strokeDasharray="3 3" vertical={false} stroke="rgba(255,255,255,0.2)" />
                    <XAxis
                        dataKey="category"
                        tick={{ fontSize: 14, fill: "#ffffff" }}
                        stroke="#ffffff"
                        interval={0}
                        angle={-45}
                        textAnchor="end"
                        height={80}
                    />
                    <YAxis
                        tick={{ fontSize: 14, fill: "#ffffff" }}
                        stroke="#ffffff"
                        tickFormatter={(value) =>
                            new Intl.NumberFormat("no-NO", { notation: "compact" }).format(value)
                        }
                    />
                    <Tooltip
                        contentStyle={{ backgroundColor: "hsl(var(--surface))", border: "1px solid hsl(var(--border))", color: "#ffffff", fontSize: 14 }}
                        formatter={(value: number) =>
                            new Intl.NumberFormat("no-NO", { style: "currency", currency: "NOK" }).format(value)
                        }
                    />
                    <Legend wrapperStyle={{ color: "#ffffff", fontSize: 14 }} />
                    <Bar dataKey="budget" name="Budsjett" fill="#9ca3af" radius={[4, 4, 0, 0]} />
                    <Bar dataKey="actual" name="Regnskap" fill="#2563eb" radius={[4, 4, 0, 0]} />
                </BarChart>
            </ResponsiveContainer>
        </div>
    )
}
