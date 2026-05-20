"use client";

import CreateJiraIssue from "../components/jira/CreateJiraIssue";
import { Lightbulb } from "lucide-react";

export default function InnspillPage() {
    return (
        <div className="mx-auto w-full max-w-3xl pb-32">
            <header className="mb-8">
                <h1 className="text-2xl font-bold tracking-tight text-foreground sm:text-3xl">
                    Innspill
                </h1>
                <p className="mt-3 max-w-2xl text-base leading-relaxed text-muted-foreground">
                    Send innspill som oppgaver i det tilkoblede oppgavestyringssystemet. Du kan følge status der som vanlig etter at saken er opprettet.
                </p>
            </header>

            <div className="overflow-hidden rounded-2xl border border-border bg-card shadow-sm">
                <div className="p-6 sm:p-8">
                    <CreateJiraIssue
                        onSuccess={(key, url) => {
                            window.open(url, "_blank");
                        }}
                    />
                </div>

                <aside className="border-t border-border bg-muted/40 px-6 py-5 sm:px-8">
                    <div className="flex gap-3">
                        <div className="mt-0.5 shrink-0 text-primary">
                            <Lightbulb className="h-5 w-5" aria-hidden />
                        </div>
                        <div className="min-w-0 space-y-3">
                            <h2 className="text-sm font-semibold text-foreground">Tips</h2>
                            <ul className="list-disc space-y-1.5 pl-4 text-sm text-muted-foreground marker:text-primary/80">
                                <li>
                                    Standard oppsett bruker prosjektet <strong className="font-medium text-foreground">KAN (BEFS)</strong>
                                </li>
                                <li>
                                    Vanlige issuetyper: <strong className="font-medium text-foreground">Epic</strong> og{" "}
                                    <strong className="font-medium text-foreground">Oppgave</strong> (avhengig av oppsett i oppgavestyring)
                                </li>
                                <li>Du kan legge til etiketter for bedre oversikt i oppgavestyringssystemet</li>
                                <li>Når en sak er opprettet, åpnes den gjerne i ny fane</li>
                            </ul>
                        </div>
                    </div>
                </aside>
            </div>
        </div>
    );
}
