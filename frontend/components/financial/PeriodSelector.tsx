"use client"

import {
    Select,
    SelectContent,
    SelectItem,
    SelectTrigger,
    SelectValue,
} from "@/components/ui/select"
import { Label } from "@/components/ui/label"

interface PeriodSelectorProps {
    year: number
    setYear: (year: number) => void
    periodType: "month" | "quarter" | "ytd" | "year"
    setPeriodType: (type: "month" | "quarter" | "ytd" | "year") => void
    periodValue: number | null
    setPeriodValue: (val: number | null) => void
}

export function PeriodSelector({
    year,
    setYear,
    periodType,
    setPeriodType,
    periodValue,
    setPeriodValue,
}: PeriodSelectorProps) {

    const years = [2026, 2025, 2024, 2023]
    const months = [
        { value: 1, label: "January" },
        { value: 2, label: "February" },
        { value: 3, label: "March" },
        { value: 4, label: "April" },
        { value: 5, label: "May" },
        { value: 6, label: "June" },
        { value: 7, label: "July" },
        { value: 8, label: "August" },
        { value: 9, label: "September" },
        { value: 10, label: "October" },
        { value: 11, label: "November" },
        { value: 12, label: "December" },
    ]
    const quarters = [
        { value: 1, label: "Q1" },
        { value: 2, label: "Q2" },
        { value: 3, label: "Q3" },
        { value: 4, label: "Q4" },
    ]

    return (
        <div className="flex gap-4 items-end">
            {/* Year Selector */}
            <div className="grid w-[120px] gap-1.5">
                <Label>Year</Label>
                <Select
                    value={year.toString()}
                    onValueChange={(val) => setYear(parseInt(val))}
                >
                    <SelectTrigger>
                        <SelectValue placeholder="Year" />
                    </SelectTrigger>
                    <SelectContent>
                        {years.map((y) => (
                            <SelectItem key={y} value={y.toString()}>
                                {y}
                            </SelectItem>
                        ))}
                    </SelectContent>
                </Select>
            </div>

            {/* Type Selector */}
            <div className="grid w-[140px] gap-1.5">
                <Label>Period Type</Label>
                <Select
                    value={periodType}
                    onValueChange={(val: any) => setPeriodType(val)}
                >
                    <SelectTrigger>
                        <SelectValue />
                    </SelectTrigger>
                    <SelectContent>
                        <SelectItem value="month">Month</SelectItem>
                        <SelectItem value="quarter">Quarter</SelectItem>
                        <SelectItem value="ytd">Year to Date</SelectItem>
                        <SelectItem value="year">Full Year</SelectItem>
                    </SelectContent>
                </Select>
            </div>

            {/* Value Selector (Month/Quarter) */}
            {(periodType === "month" || periodType === "ytd") && (
                <div className="grid w-[140px] gap-1.5">
                    <Label>{periodType === "ytd" ? "Up to Month" : "Month"}</Label>
                    <Select
                        value={periodValue?.toString() || ""}
                        onValueChange={(val) => setPeriodValue(parseInt(val))}
                    >
                        <SelectTrigger>
                            <SelectValue placeholder="Select Month" />
                        </SelectTrigger>
                        <SelectContent>
                            {months.map((m) => (
                                <SelectItem key={m.value} value={m.value.toString()}>
                                    {m.label}
                                </SelectItem>
                            ))}
                        </SelectContent>
                    </Select>
                </div>
            )}

            {periodType === "quarter" && (
                <div className="grid w-[140px] gap-1.5">
                    <Label>Quarter</Label>
                    <Select
                        value={periodValue?.toString() || ""}
                        onValueChange={(val) => setPeriodValue(parseInt(val))}
                    >
                        <SelectTrigger>
                            <SelectValue placeholder="Select Quarter" />
                        </SelectTrigger>
                        <SelectContent>
                            {quarters.map((q) => (
                                <SelectItem key={q.value} value={q.value.toString()}>
                                    {q.label}
                                </SelectItem>
                            ))}
                        </SelectContent>
                    </Select>
                </div>
            )}
        </div>
    )
}
