"use client";

import { MessageCircle } from "lucide-react";
import { OPEN_KI_KOLLEGA_EVENT } from "@/app/components/features/ChatWidget";

export default function KiKollegaHelpPanel() {
    const openChat = () => {
        window.dispatchEvent(new CustomEvent(OPEN_KI_KOLLEGA_EVENT));
    };

    return (
        <div className="glass-card border border-border p-6 sm:p-8 max-w-2xl">
            <div className="flex items-start gap-4">
                <div className="p-3 rounded-xl bg-primary/10 text-primary border border-primary/20">
                    <MessageCircle className="w-8 h-8" aria-hidden />
                </div>
                <div className="min-w-0 space-y-3">
                    <h2 className="text-xl font-semibold text-foreground">KI Kollega</h2>
                    <p className="text-muted-foreground leading-relaxed">
                        Dette er samme assistent som den blå <strong className="text-foreground">«KI kollega»</strong>
                        -knappen nede til høyre på alle sider. Du kan spørre om eiendommer, kontrakter, tall og
                        prosesser – svarene bygger på data i BEFS der det er tilgjengelig.
                    </p>
                    <ul className="list-disc list-inside text-sm text-muted-foreground space-y-1.5">
                        <li>Eksempel: «Hvilke kontrakter i Region Øst går ut i neste halvår?»</li>
                        <li>Eksempel: «Forklar kort hva risikobildet viser.»</li>
                    </ul>
                    <button
                        type="button"
                        onClick={openChat}
                        className="inline-flex items-center gap-2 rounded-lg bg-primary px-4 py-2.5 text-sm font-medium text-primary-foreground shadow-sm hover:bg-primary/90 transition-colors"
                    >
                        <MessageCircle className="w-4 h-4" aria-hidden />
                        Åpne KI Kollega
                    </button>
                </div>
            </div>
        </div>
    );
}
