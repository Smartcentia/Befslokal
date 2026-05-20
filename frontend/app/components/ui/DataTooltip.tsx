"use client";

import React from "react";

interface DataTooltipProps {
    content: string;
    children: React.ReactNode;
    className?: string;
    as?: "span" | "div";
}

export default function DataTooltip({ children }: DataTooltipProps) {
    return <>{children}</>;
}
