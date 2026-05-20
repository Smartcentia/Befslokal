import React from 'react';
import { cn } from "@/lib/utils";
import { Loader2 } from "lucide-react";

interface ButtonProps extends React.ButtonHTMLAttributes<HTMLButtonElement> {
    children: React.ReactNode;
    isLoading?: boolean;
    variant?: 'primary' | 'secondary' | 'ghost' | 'outline';
    size?: 'sm' | 'md' | 'lg' | 'icon';
}

export function Button({
    children,
    className,
    isLoading,
    variant = 'primary',
    size = 'md',
    disabled,
    ...props
}: ButtonProps) {

    const variants = {
        primary: "bg-[#FF8BA7] text-white hover:bg-[#FF7A9A] shadow-sm shadow-[#FF8BA7]/30",
        secondary: "bg-[#C4B5FD] text-white hover:bg-[#B5A4FC]",
        ghost: "bg-transparent text-gray-600 hover:bg-gray-100",
        outline: "bg-transparent border border-gray-200 text-gray-600 hover:bg-gray-50",
    };

    const sizes = {
        sm: "px-3 py-1.5 text-xs",
        md: "px-6 py-3 text-sm font-medium",
        lg: "px-8 py-4 text-base font-medium",
        icon: "p-2",
    };

    return (
        <button
            disabled={isLoading || disabled}
            className={cn(
                "relative inline-flex items-center justify-center rounded-2xl transition-all duration-200 disabled:opacity-50 disabled:cursor-not-allowed active:scale-[0.98]",
                variants[variant],
                sizes[size],
                className
            )}
            {...props}
        >
            {isLoading && <Loader2 className="w-4 h-4 mr-2 animate-spin" />}
            {children}
        </button>
    );
}
