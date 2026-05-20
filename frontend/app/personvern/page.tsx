import type { Metadata } from "next";

export const metadata: Metadata = {
  title: "Personvern",
};

export default function PrivacyPage() {
  return (
    <main className="max-w-3xl mx-auto py-12 px-6 space-y-8">
      <header>
        <h1 className="text-3xl font-bold tracking-tight text-foreground">Personvern i BEFS</h1>
        <p className="mt-2 text-sm text-muted-foreground">
          Her finner du overordnet informasjon om hvordan BEFS behandler personopplysninger og
          hvilke prinsipper som gjelder for bruk av systemet.
        </p>
      </header>

      <section className="space-y-3">
        <h2 className="text-xl font-semibold text-foreground">Formål med behandlingen</h2>
        <p className="text-sm text-foreground">
          BEFS brukes til forvaltning av eiendommer, kontrakter og tilknyttede prosesser i Bufetat.
          Systemet er ikke rettet mot allmennheten, men mot autoriserte brukere i tjenesten.
        </p>
      </section>

      <section className="space-y-3">
        <h2 className="text-xl font-semibold text-foreground">Ansvarlig for behandlingen</h2>
        <p className="text-sm text-foreground">
          Bufetat er behandlingsansvarlig for personopplysninger som behandles i BEFS. Mer detaljert
          informasjon om behandlingsgrunnlag og rettigheter gis gjennom Bufetats ordinære
          personverndokumentasjon.
        </p>
      </section>

      <section className="space-y-3">
        <h2 className="text-xl font-semibold text-foreground">Informasjonskapsler (cookies)</h2>
        <p className="text-sm text-foreground">
          BEFS benytter tekniske informasjonskapsler for å håndtere innlogging og sesjon. Det brukes
          ikke cookies til markedsføring eller sporing av brukere utenfor systemet.
        </p>
      </section>
    </main>
  );
}

