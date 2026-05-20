# BEFS Frontend

## Oversikt
Dette er frontend for "Bufetat Eiendomsforvaltningssystem" (BEFS), bygget med Next.js (App Router).

## Oppsett for utvikling

1. **Installer avhengigheter**:
    ```bash
    cd frontend
    npm install
    ```

2. **Miljøvariabler**:
    Kopier `.env.example` til `.env.local` og konfigurer:
    ```bash
    cp .env.example .env.local
    ```
    
    Viktige variabler:
    - `NEXT_PUBLIC_MAPBOX_ACCESS_TOKEN`: Påkrevd for kart.
    - `NEXT_PUBLIC_API_URL`: URL til backend API (standard: http://localhost:8000/api/v1).
    - `NEXTAUTH_SECRET`: Hemmelighet for NextAuth session-kryptering.

3. **Kjør utviklingsserveren**:
    ```bash
    npm run dev
    ```

Åpne [http://localhost:3000](http://localhost:3000) i nettleseren.

## Distribusjon
Frontenden er satt opp for automatisk distribusjon til Vercel ved push til `main`-branchen.
