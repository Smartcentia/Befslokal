import type { Metadata } from "next";

export const metadata: Metadata = {
    title: "Innspill",
    description: "Opprett innspill til oppgavestyring fra BEFS.",
};

export default function InnspillLayout({ children }: { children: React.ReactNode }) {
    return children;
}
