"use client";
import { ReactNode } from "react";
interface Props { minHeight?: number; className?: string; children?: ReactNode; }
export function LazyMap({ className, children }: Props) {
    return <div className={className}>{children}</div>;
}
