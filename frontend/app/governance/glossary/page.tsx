"use client";

import React from "react";
import GlossaryComponent from "@/components/governance/GlossaryComponent";
import Header from "@/app/components/ui/Header";

export default function GlossaryPage() {
    return (
        <div className="min-h-screen bg-gray-50 flex flex-col">
            <Header />
            <main className="flex-1 container mx-auto p-6">
                <GlossaryComponent />
            </main>
        </div>
    );
}
