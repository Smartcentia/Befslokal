import type { Metadata } from "next";
import { AgressoCsvLab } from "./AgressoCsvLab";

export const metadata: Metadata = {
  title: "Agresso CSV-lab",
  description:
    "Last inn Agresso CSV, se kolonneforklaringer, flagg mulige avvik og kopier prompt for vurdering.",
};

export default function AgressoCsvPage() {
  return <AgressoCsvLab />;
}
