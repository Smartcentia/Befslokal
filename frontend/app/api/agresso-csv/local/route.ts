import { readFile } from "node:fs/promises";
import { NextResponse } from "next/server";

/**
 * Server-side lesing av lokal Agresso-CSV (kun utvikling).
 * Sett AGRESSO_CSV_PATH i .env.local til full sti til filen.
 * Aktiver auto-innlasting i UI med NEXT_PUBLIC_AUTO_LOAD_AGRESSO_CSV=1
 */
export async function GET() {
  if (process.env.NODE_ENV !== "development") {
    return NextResponse.json(
      { error: "Kun tilgjengelig i development." },
      { status: 403 },
    );
  }

  const filePath = process.env.AGRESSO_CSV_PATH?.trim().replace(/^["']|["']$/g, "");
  if (!filePath) {
    return NextResponse.json(
      {
        error:
          "Mangler AGRESSO_CSV_PATH i .env.local (full sti til CSV-filen).",
      },
      { status: 404 },
    );
  }

  try {
    const buf = await readFile(filePath);
    const text = buf.toString("utf-8");
    return new NextResponse(text, {
      status: 200,
      headers: {
        "Content-Type": "text/csv; charset=utf-8",
        "Cache-Control": "no-store",
      },
    });
  } catch (e) {
    const msg = e instanceof Error ? e.message : "Ukjent feil";
    return NextResponse.json(
      { error: `Kunne ikke lese fil: ${msg}` },
      { status: 500 },
    );
  }
}
