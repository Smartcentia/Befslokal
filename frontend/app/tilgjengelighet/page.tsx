import type { Metadata } from "next";

export const metadata: Metadata = {
  title: "Tilgjengelighet",
};

export default function AccessibilityPage() {
  return (
    <main className="max-w-3xl mx-auto py-12 px-6 space-y-8">
      <header>
        <h1 className="text-3xl font-bold tracking-tight text-foreground">
          Tilgjengelighetserklæring for BEFS
        </h1>
        <p className="mt-2 text-sm text-muted-foreground">
          Denne siden beskriver hvordan BEFS (Bufetat eiendomsforvaltningssystem) jobber med
          universell utforming og hvilke kjente avvik som finnes.
        </p>
      </header>

      <section className="space-y-3">
        <h2 className="text-xl font-semibold text-foreground">Status</h2>
        <p className="text-sm text-foreground">
          Løsningen er under aktiv utvikling. Vi jobber for å oppfylle kravene i WCAG 2.1 nivå AA,
          i tråd med kravene til offentlige virksomheter i Norge.
        </p>
      </section>

      <section className="space-y-3">
        <h2 className="text-xl font-semibold text-foreground">Kjente forbedringsområder</h2>
        <ul className="list-disc pl-5 space-y-2 text-sm text-foreground">
          <li>Videre forbedring av tastaturnavigasjon i enkelte modaler og dialoger.</li>
          <li>Systematisk gjennomgang av kontrast i alle tema-varianter.</li>
          <li>Flere skjermleser-etiketter på interaktive kart og diagrammer.</li>
        </ul>
      </section>

      <section className="space-y-3">
        <h2 className="text-xl font-semibold text-foreground">Gi tilbakemelding</h2>
        <p className="text-sm text-foreground">
          Opplever du barrierer når du bruker BEFS, eller har du forslag til forbedringer, ønsker
          vi å høre fra deg. Ta kontakt med systemansvarlig i Bufetat via etablerte
          kontaktkanaler.
        </p>
      </section>
    </main>
  );
}

