import React from 'react';
import { cn } from "@/lib/utils";

interface CardProps extends React.HTMLAttributes<HTMLDivElement> {
    children: React.ReactNode;
    className?: string;
    gradient?: boolean;
}

export function Card({ children, className, gradient = false, ...props }: CardProps) {
    return (
        <div
            className={cn(
                "rounded-3xl p-6 transition-all duration-300 backdrop-blur-xl",
                "bg-[var(--glass-bg)] border border-[var(--glass-border)] shadow-[var(--card-shadow)]",
                "hover:border-[var(--glass-highlight)] hover:shadow-[var(--card-shadow-hover)]",
                gradient && "bg-gradient-to-br from-[var(--glass-bg)] to-[var(--glass-highlight)]",
                className
            )}
            {...props}
        >
            {children}
        </div>
    );
}
