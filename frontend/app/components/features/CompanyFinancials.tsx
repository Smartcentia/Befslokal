import React, { useEffect, useState } from 'react';
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card";
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table";
import { Badge } from "@/components/ui/badge";
import { Skeleton } from "@/components/ui/skeleton";
import { TrendingUp, TrendingDown, DollarSign, Activity } from "lucide-react";
import { externalApiUrl } from '@/lib/api/client';
import { supabase } from '@/lib/supabase';

interface FinancialData {
    year: string;
    currency: string;
    revenue: number | null;
    operating_profit: number | null;
    net_income: number | null;
    equity: number | null;
    total_assets: number | null;
    liquidity_ratio: number | null;
}

interface CompanyFinancialsProps {
    orgNr: string;
    companyName?: string;
}

export function CompanyFinancials({ orgNr, companyName }: CompanyFinancialsProps) {
    const [data, setData] = useState<FinancialData[]>([]);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState<string | null>(null);

    useEffect(() => {
        if (!orgNr) return;

        const fetchData = async () => {
            setLoading(true);
            setError(null);
            try {
                const { data: { session } } = await supabase.auth.getSession();
                const bearer =
                    process.env.NEXT_PUBLIC_BACKEND_SECRET || 'befs-super-secret-key-12345';
                const headers: Record<string, string> = {
                    'Content-Type': 'application/json',
                    Authorization: `Bearer ${bearer}`,
                };
                if (typeof window !== 'undefined') {
                    const impersonateEmail = localStorage.getItem('impersonate_email');
                    if (impersonateEmail) {
                        headers['X-Impersonate-Email'] = impersonateEmail;
                    } else if (session?.user?.email) {
                        headers['X-User-Email'] = session.user.email;
                    }
                }

                const url = externalApiUrl(`/brreg/${orgNr}/regnskap`);
                const response = await fetch(url, {
                    headers,
                    credentials: 'include',
                    cache: 'no-store',
                });

                if (!response.ok) {
                    if (response.status === 404) {
                        setData([]); // No data found is valid
                        return;
                    }
                    throw new Error(`Failed to fetch financials: ${response.status}`);
                }

                const result = await response.json();
                setData(result.financials || []);
            } catch (err) {
                console.error("Error fetching financials:", err);
                setError("Kunne ikke hente regnskapstall.");
            } finally {
                setLoading(false);
            }
        };

        fetchData();
    }, [orgNr]);

    if (loading) {
        return <Skeleton className="h-[300px] w-full" />;
    }

    if (error) {
        return (
            <Card>
                <CardContent className="pt-6">
                    <div className="text-red-500 text-sm">{error}</div>
                </CardContent>
            </Card>
        );
    }

    if (!data || data.length === 0) {
        return (
            <Card>
                <CardHeader>
                    <CardTitle>Økonomi</CardTitle>
                    <CardDescription>Ingen regnskapstall funnet for {companyName || orgNr}</CardDescription>
                </CardHeader>
            </Card>
        );
    }

    // Helper to format currency
    const formatCurrency = (val: number | null, currency: string) => {
        if (val === null || val === undefined) return "-";
        // Shorten large numbers: 1 000 000 -> 1.0 MNOK
        if (Math.abs(val) >= 1000000) {
            return `${(val / 1000000).toFixed(1)} M${currency}`;
        }
        return new Intl.NumberFormat('no-NO', { style: 'currency', currency }).format(val);
    };

    const getProfitBadge = (profit: number | null) => {
        if (profit === null) return null;
        if (profit > 0) return <Badge variant="default" className="bg-green-600 hover:bg-green-700"><TrendingUp className="w-3 h-3 mr-1" /> Overskudd</Badge>;
        return <Badge variant="destructive"><TrendingDown className="w-3 h-3 mr-1" /> Underskudd</Badge>;
    };

    return (
        <Card className="w-full">
            <CardHeader>
                <div className="flex justify-between items-center">
                    <div>
                        <CardTitle className="flex items-center gap-2">
                            <DollarSign className="w-5 h-5" />
                            Nøkkeltall
                        </CardTitle>
                        <CardDescription>
                            Årsregnskap for {companyName || orgNr} (Kilde: Brønnøysundregistrene)
                        </CardDescription>
                    </div>
                    <Activity className="w-4 h-4 text-muted-foreground" />
                </div>
            </CardHeader>
            <CardContent>
                <Table>
                    <TableHeader>
                        <TableRow>
                            <TableHead>År</TableHead>
                            <TableHead className="text-right">Driftsinntekter</TableHead>
                            <TableHead className="text-right">Driftsresultat</TableHead>
                            <TableHead className="text-right">Årsresultat</TableHead>
                            <TableHead className="text-right">Egenkapital</TableHead>
                        </TableRow>
                    </TableHeader>
                    <TableBody>
                        {data.map((yearData) => (
                            <TableRow key={yearData.year}>
                                <TableCell className="font-medium">{yearData.year}</TableCell>
                                <TableCell className="text-right">{formatCurrency(yearData.revenue, yearData.currency)}</TableCell>
                                <TableCell className="text-right font-semibold">
                                    {formatCurrency(yearData.operating_profit, yearData.currency)}
                                </TableCell>
                                <TableCell className="text-right flex justify-end gap-2 items-center">
                                    {formatCurrency(yearData.net_income, yearData.currency)}
                                    {getProfitBadge(yearData.net_income)}
                                </TableCell>
                                <TableCell className="text-right">{formatCurrency(yearData.equity, yearData.currency)}</TableCell>
                            </TableRow>
                        ))}
                    </TableBody>
                </Table>
            </CardContent>
        </Card>
    );
}
