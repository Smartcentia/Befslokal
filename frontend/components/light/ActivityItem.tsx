import React from 'react';
import { cn } from "@/lib/utils";

interface ActivityItemProps {
    time: string;
    title: string;
    description: string;
    color?: string; // Tailwind text color class
    isLast?: boolean;
}

export function ActivityItem({ time, title, description, color = "text-blue-500", isLast }: ActivityItemProps) {
    return (
        <div className="flex gap-4 group">
            {/* Time Column */}
            <div className={cn("w-16 pt-1 text-sm font-medium transition-colors group-hover:text-foreground", color)}>
                {time}
            </div>

            {/* Timeline Line & Content */}
            <div className="relative flex-1 pb-8">
                {!isLast && (
                    <div className="absolute top-3 left-[5px] w-[2px] h-full bg-gray-100 -z-10" />
                )}

                <div className="flex items-start gap-4">
                    <div className={cn("mt-1.5 w-2.5 h-2.5 rounded-full ring-4 ring-white", color.replace('text-', 'bg-'))} />

                    <div>
                        <h4 className="font-semibold text-gray-900">{title}</h4>
                        <p className="text-sm text-gray-500 mt-0.5">{description}</p>
                    </div>
                </div>
            </div>
        </div>
    );
}
