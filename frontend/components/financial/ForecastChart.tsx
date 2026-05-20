"use client"

import {
    ComposedChart,
    Line,
    XAxis,
    YAxis,
    CartesianGrid,
    Tooltip,
    Legend,
    ResponsiveContainer,
    Area,
} from "recharts"

interface ForecastItem {
    date: string // YYYY-MM
    amount: number
    type: "actual" | "forecast"
    lower_bound?: number
    upper_bound?: number
}

interface ForecastChartProps {
    data: ForecastItem[];
}

export function ForecastChart({ data }: ForecastChartProps) {
    // Preprocess data to separate lines if needed, or rely on distinct data keys?
    // Recharts trick: We can use a single array, but different data keys for actual vs forecast?
    // Or simpler: Single line, but use 'strokeDasharray' based on type? 
    // Recharts `Line` doesn't support varying stroke dashboard easily per point.
    // approach: Two lines. One "Actual" line, One "Forecast" line.
    // The Data array needs to have both keys for the transition point to connect them.

    const chartData = data.map(item => ({
        ...item,
        actualAmount: item.type === 'actual' ? item.amount : null,
        // For forecast line to connect to last actual, we might need a bridge, 
        // but for simplicity, let's just plot them. 
        // If there is a gap, we might need to duplicate the last actual point as the first forecast point.
        forecastAmount: item.type === 'forecast' ? item.amount : null,
        range: item.type === 'forecast' ? [item.lower_bound, item.upper_bound] : null
    }));

    return (
        <div className="h-100 w-full">
            <ResponsiveContainer width="100%" height="100%">
                <ComposedChart
                    data={chartData}
                    margin={{
                        top: 20,
                        right: 30,
                        left: 20,
                        bottom: 5,
                    }}
                >
                    <CartesianGrid strokeDasharray="3 3" vertical={false} stroke="#374151" />
                    <XAxis
                        dataKey="date"
                        tick={{ fontSize: 12 }}
                        interval="preserveStartEnd"
                        minTickGap={30}
                    />
                    <YAxis
                        tickFormatter={(value) =>
                            new Intl.NumberFormat("no-NO", { notation: "compact" }).format(value)
                        }
                    />
                    <Tooltip
                        contentStyle={{ backgroundColor: '#1f2937', border: 'none' }}
                        itemStyle={{ color: '#e5e7eb' }}
                        formatter={(value: number) =>
                            new Intl.NumberFormat("no-NO", { style: "currency", currency: "NOK", maximumFractionDigits: 0 }).format(value)
                        }
                    />
                    <Legend />

                    <Line
                        type="monotone"
                        dataKey="actualAmount"
                        name="Historisk (Faktisk)"
                        stroke="#3b82f6"
                        strokeWidth={3}
                        dot={{ r: 4 }}
                        connectNulls={true}
                    />

                    <Line
                        type="monotone"
                        dataKey="forecastAmount"
                        name="Prognose"
                        stroke="#10b981"
                        strokeWidth={3}
                        strokeDasharray="5 5"
                        dot={{ r: 4 }}
                        connectNulls={true}
                    />

                    {/* Optional Area for Confidence Interval if we can map it correctly
               Area typically expects [min, max] values in the key or separate keys
            */}
                </ComposedChart>
            </ResponsiveContainer>
        </div>
    )
}
