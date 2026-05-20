import React from 'react';

interface StatRingProps {
    percentage: number;
    label: string;
    size?: number;
    strokeWidth?: number;
    color?: string;
}

export function StatRing({
    percentage,
    label,
    size = 120,
    strokeWidth = 8,
    color = "#C4B5FD"
}: StatRingProps) {
    const radius = (size - strokeWidth) / 2;
    const circumference = radius * 2 * Math.PI;
    const offset = circumference - (percentage / 100) * circumference;

    return (
        <div className="relative flex items-center justify-center" style={{ width: size, height: size }}>
            <svg className="transform -rotate-90 w-full h-full">
                {/* Background Circle */}
                <circle
                    className="text-gray-100"
                    stroke="currentColor"
                    strokeWidth={strokeWidth}
                    fill="transparent"
                    r={radius}
                    cx={size / 2}
                    cy={size / 2}
                />
                {/* Progress Circle */}
                <circle
                    stroke={color}
                    strokeWidth={strokeWidth}
                    strokeDasharray={circumference}
                    strokeDashoffset={offset}
                    strokeLinecap="round"
                    fill="transparent"
                    r={radius}
                    cx={size / 2}
                    cy={size / 2}
                    className="transition-all duration-1000 ease-out"
                />
            </svg>
            <div className="absolute flex flex-col items-center">
                <span className="text-2xl font-bold text-gray-800">{percentage}%</span>
                <span className="text-xs text-gray-500 uppercase font-medium">{label}</span>
            </div>
        </div>
    );
}
