"use client";

import React, { useEffect, useState } from 'react';
import { 
  Radar, 
  RadarChart, 
  PolarGrid, 
  PolarAngleAxis, 
  PolarRadiusAxis, 
  ResponsiveContainer, 
  Tooltip, 
  Legend 
} from 'recharts';
import { fetchAPI } from '@/lib/api/client';

interface ActivityItem {
    name: string;
    total: number;
    completed: number;
    open: number;
    overdue: number;
}

interface SummaryData {
    items: ActivityItem[];
    total_cases: number;
}

export default function ActivityWheel() {
    const [data, setData] = useState<SummaryData | null>(null);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState<string | null>(null);

    useEffect(() => {
        fetchAPI('/internal-control/summary')
            .then(setData)
            .catch(err => {
                console.error("Failed to fetch activity summary:", err);
                setError("Kunne ikke laste aktivitetsdata");
            })
            .finally(() => setLoading(false));
    }, []);

    if (loading) return (
        <div className="h-full flex flex-col items-center justify-center space-y-2">
            <div className="w-8 h-8 border-4 border-primary/30 border-t-primary rounded-full animate-spin"></div>
            <p className="text-[10px] text-muted uppercase tracking-tighter">Laster aktiviteter...</p>
        </div>
    );
    
    if (error) return (
        <div className="h-full flex items-center justify-center text-danger text-xs italic">
            {error}
        </div>
    );

    if (!data || !data.items || data.items.length === 0) return (
        <div className="h-full flex flex-col items-center justify-center text-muted text-sm p-4 text-center">
            <p className="opacity-50 italic">Ingen planlagte aktiviteter funnet for dine eiendommer.</p>
        </div>
    );

    // Prepare data for Radar Chart
    const chartData = data.items.map(item => ({
        subject: item.name,
        total: item.total,
        completed: item.completed,
        overdue: item.overdue,
        fullMark: Math.max(...data.items.map(i => i.total), 5)
    }));

    const overdueTotal = data.items.reduce((acc, i) => acc + i.overdue, 0);

    return (
        <div className="w-full h-full flex flex-col p-2">
            <div className="mb-2">
                <h3 className="text-lg font-bold text-foreground">Aktivitetsstatus</h3>
                <p className="text-xs text-muted-foreground">Internkontroll og HMS-oppgaver</p>
            </div>
            <div className="grow">
                <ResponsiveContainer width="100%" height="100%">
                    <RadarChart cx="50%" cy="50%" outerRadius="70%" data={chartData}>
                        <PolarGrid stroke="rgba(255,255,255,0.05)" />
                        <PolarAngleAxis 
                            dataKey="subject" 
                            tick={{ fill: '#94a3b8', fontSize: 10, fontWeight: 500 }} 
                        />
                        <PolarRadiusAxis 
                            angle={30} 
                            domain={[0, 'auto']} 
                            tick={false} 
                            axisLine={false} 
                        />
                        <Radar
                            name="Totalt"
                            dataKey="total"
                            stroke="#3b82f6"
                            fill="#3b82f6"
                            fillOpacity={0.3}
                        />
                        <Radar
                            name="Fullført"
                            dataKey="completed"
                            stroke="#10b981"
                            fill="#10b981"
                            fillOpacity={0.5}
                        />
                         <Radar
                            name="Forfalt"
                            dataKey="overdue"
                            stroke="#ef4444"
                            fill="#ef4444"
                            fillOpacity={0.4}
                        />
                        <Tooltip 
                            contentStyle={{ 
                                backgroundColor: 'rgba(15, 23, 42, 0.95)', 
                                borderColor: 'rgba(255,255,255,0.1)',
                                borderRadius: '12px',
                                fontSize: '11px',
                                boxShadow: '0 10px 15px -3px rgba(0, 0, 0, 0.5)'
                            }}
                            itemStyle={{ padding: '0px' }}
                        />
                        <Legend 
                            wrapperStyle={{ fontSize: '10px', paddingTop: '10px' }}
                            iconType="circle"
                        />
                    </RadarChart>
                </ResponsiveContainer>
            </div>
            <div className="mt-2 pt-2 border-t border-white/5 flex items-center justify-between text-[10px] text-muted-foreground uppercase tracking-widest font-medium">
                <span>{data.total_cases} OPPGAVER TOTALT</span>
                <span className={overdueTotal > 0 ? "text-danger font-bold" : ""}>
                    {overdueTotal} FORFALTE
                </span>
            </div>
        </div>
    );
}
