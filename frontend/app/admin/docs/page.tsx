"use client";

import React, { useEffect, useState } from 'react';
import ReactMarkdown from 'react-markdown';
import { FileText, ArrowLeft, Terminal, Bot, Database, Rocket, RefreshCw, AlertTriangle, Plus, Archive } from 'lucide-react';
import Link from 'next/link';
import { fetchAPI } from '@/lib/api';

interface CommandDoc {
    id: string;
    title: string;
    description: string;
    content: string;
    icon: string;
}

const COMMAND_DOCS: CommandDoc[] = [
    {
        id: 'ki-kollega',
        title: 'KI Kollega',
        description: 'Context-aware AI assistant arkitektur',
        icon: 'bot',
        content: `# KI Kollega - AI Assistant

Context-aware AI chat assistant for the BEFS platform.

## Arkitektur

### Backend
- **Service**: \`app/services/ki_kollega/service.py\`
- **API Router**: \`app/api/v1/ai/chat.py\`

### Frontend
- **Service**: \`lib/domains/innsikt/kiKollegaService.ts\`
- **Widget**: \`app/components/features/ChatWidget.tsx\`
- **Interface**: \`app/components/features/ChatInterface.tsx\`

## API Endpoints

| Endpoint | Method | Beskrivelse |
|----------|--------|-------------|
| \`/api/v1/ai/chat\` | POST | Hoved chat endpoint |
| \`/api/v1/ai/chat/stream\` | POST | Streaming response (SSE) |
| \`/api/v1/ai/suggestions\` | GET | Kontekst-avhengige forslag |
| \`/api/v1/ai/health\` | GET | Health check |

## Kontekst-ekstraksjon

Frontend ekstraherer kontekst fra URL path:
- \`/properties/123\` → \`{ entity_type: "property", entity_id: "123" }\`
- \`/contracts/456\` → \`{ entity_type: "contract", entity_id: "456" }\`
- \`/parties/789\` → \`{ entity_type: "party", entity_id: "789" }\`

Dette lar brukere spørre "Hva er arealet?" uten å spesifisere eiendom.

## Spørringstyper

KI Kollega klassifiserer spørringer:
- **lookup**: Finne spesifikke data
- **comparison**: Sammenligne entiteter
- **analysis**: Trendanalyse, aggregeringer
- **explanation**: Forklare konsepter/scorer
- **action**: Utløse arbeidsflyter
- **general**: Generelle spørsmål

## Funksjoner

1. **Hybrid retrieval**: Søker i både database og dokumenter
2. **Oppfølgingsspørsmål**: Foreslår relevante neste spørsmål
3. **Kildehenvisninger**: Viser hvilke entiteter som ble brukt
4. **Text-to-speech**: Norsk opplesning
5. **Samtalehistorikk**: Holder kontekst mellom meldinger`
    },
    {
        id: 'deploy-backend',
        title: 'Deploy Backend',
        description: 'Deploy backend til Railway',
        icon: 'rocket',
        content: `# Deploy Backend

Backend kjører på **Railway**..

## Deploy

- **Auto:** \`git push origin main\` – Railway deployer automatisk via git push.
- **Manuelt:** \`cd backend && railway up --detach\`.

## Verifiser

Bruk URL til den tjenesten du bruker:

\`\`\`bash
# BEFS1:
curl https://striking-insight-production-a21b.up.railway.app/api/v1/health

# Eller knowme-backend-prod:
# (gammel Render URL - ikke lenger i bruk)
\`\`\`

## Viktig

- **Backend-URL:** Sett \`NEXT_PUBLIC_API_URL\` i Vercel (base-URL uten /api/v1). Ingen fallback – må være satt.
- **BACKEND_SECRET** (Railway) og **NEXTAUTH_SECRET** (Vercel) må være identiske.
- Sjekk logs: \`railway logs --tail 30\`.`
    },
    {
        id: 'deploy-frontend',
        title: 'Deploy Frontend',
        description: 'Deploy frontend til Vercel',
        icon: 'rocket',
        content: `# Deploy Frontend

Deploy frontend til Vercel (auto-deploy via git).

## Kommandoer

\`\`\`bash
cd KNOWME/frontend
git push origin main  # Auto-deploys
\`\`\`

## Verifiser

\`\`\`bash
curl https://knowme-frontend-amber.vercel.app/api/health
\`\`\`

## Viktig

- Vercel deployer automatisk ved push til main
- Lokal utvikling: \`npm run dev\` i frontend-mappen`
    },
    {
        id: 'database',
        title: 'Database',
        description: 'Database-operasjoner og migrasjoner',
        icon: 'database',
        content: `# Database Operasjoner

PostgreSQL database i skyen (serverless).

## Tilkoblinginfo

- **Host**: Serverless Cloud DB
- **Database**: \`knowme\`
- **Driver**: \`asyncpg\` (async SQLAlchemy)

## Kjør Migrasjoner

\`\`\`bash
cd backend
alembic upgrade head
\`\`\`

## Opprett Ny Migrasjon

\`\`\`bash
alembic revision --autogenerate -m "beskrivelse av endring"
\`\`\`

## Nøkkeltabeller

| Tabell | Beskrivelse |
|--------|-------------|
| \`properties\` | Eiendommer |
| \`contracts\` | Kontrakter |
| \`parties\` | Parter (leietakere, eiere) |
| \`deviations\` | Avvik (FDV) |
| \`risk_assessments\` | Risikovurderinger |
| \`units\` | Enheter (leiligheter, lokaler) |`
    },
    {
        id: 'add-feature',
        title: 'Ny Feature',
        description: 'Guide for å legge til nye features',
        icon: 'plus',
        content: `# Legg til Ny Feature

## Backend (API Endpoint)

### 1. Opprett Schema
\`\`\`python
# app/schemas/my_feature.py
from pydantic import BaseModel

class MyFeatureResponse(BaseModel):
    id: str
    name: str
\`\`\`

### 2. Opprett Router
\`\`\`python
# app/api/v1/my_feature.py
from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

router = APIRouter()

@router.get("/my-feature/{id}")
async def get_my_feature(id: str, db: AsyncSession = Depends(get_session)):
    pass
\`\`\`

### 3. Registrer i main.py
\`\`\`python
from app.api.v1.my_feature import router as my_feature_router
app.include_router(my_feature_router, prefix="/api/v1", tags=["My Feature"])
\`\`\`

## Frontend (Service + Komponent)

### 1. Opprett Service
\`\`\`typescript
// lib/domains/<domain>/myFeatureService.ts
import { fetchAPI } from '../../api/client';

export const myFeatureService = {
    getById: async (id: string) => fetchAPI(\`/my-feature/\${id}\`)
};
\`\`\`

### 2. Eksporter fra api.ts
\`\`\`typescript
export * from './domains/<domain>/myFeatureService';
\`\`\`

## Viktige Mønstre

- **Alltid bruk service layer** - aldri direkte fetch i komponenter
- **Async/await** - både frontend og backend
- **Norsk UI** - all brukerrettet tekst på norsk`
    },
    {
        id: 'troubleshoot',
        title: 'Feilsøking',
        description: 'Vanlige problemer og løsninger',
        icon: 'alert',
        content: `# Feilsøking

## Backend Problemer

### Backend starter ikke
- Sjekk Railway: \`railway logs --tail 30\`
- Verifiser miljøvariabler (DATABASE_URL, SECRET_KEY)

### Database-tilkobling feiler
1. Sjekk \`DATABASE_URL\` miljøvariabel i Railway
2. Verifiser at databasen kjører og er tilgjengelig

### Health check feiler
Vanlige årsaker:
- Database-tilkoblingsproblem
- Manglende miljøvariabler (DATABASE_URL, SECRET_KEY)
- Import-feil i Python-kode

### Kostnadsanalyse viser "Mangler husleiedata"
- Sjekk at eiendommen har \`external_data.financials.rent_summary\` for syntetisk fallback
- Eller legg til enheter og kontrakter

## Frontend Problemer

### Build feiler
Vanlige årsaker:
- TypeScript-feil
- Manglende avhengigheter
- Import path-problemer

### API-kall feiler
1. Sjekk at \`NEXT_PUBLIC_API_URL\` er korrekt
2. Verifiser at backend er healthy
3. Sjekk CORS-innstillinger

## KI Kollega Problemer

### Chat svarer ikke
1. Sjekk AI health endpoint: \`GET /api/v1/ai/health\`
2. Verifiser OpenAI credentials
3. Sjekk quota-grenser på OpenAI

### Feil kontekst
- Verifiser URL path har riktig format
- Sjekk \`extractContextFromPath()\` i kiKollegaService.ts`
    }
];

const ICONS: Record<string, any> = {
    'bot': Bot,
    'rocket': Rocket,
    'refresh': RefreshCw,
    'database': Database,
    'plus': Plus,
    'alert': AlertTriangle,
    'terminal': Terminal
};

const ARKIV_OVERVIEW_MD = `# Historisk dokumentasjon (arkiv)

Utdatert dokumentasjon er flyttet til mappen **\`arkiv/\`** i prosjektet for å holde root og backend ryddig. Innholdet er beholdt som referanse.

## Kategorier i arkiv

| Mappe | Innhold |
|-------|--------|
| \`arkiv/deploy_og_render/\` | Deploy, Render, secrets, migrering (23 filer) |
| \`arkiv/auth_og_login/\` | Login-fiks, session, 401, NextAuth (23 filer) |
| \`arkiv/rbac_og_roller/\` | RBAC-faser, brukerrettigheter (15 filer) |
| \`arkiv/google_og_email/\` | Google login, e-postverifikasjon, MFA (6 filer) |
| \`arkiv/diagnostikk_og_test/\` | Diagnostikk- og testdokumenter (11 filer) |
| \`arkiv/diverse_historisk/\` | Øvrige guider og oppsummeringer (21 filer) |
| \`arkiv/backend_deploy_fix/\` | Utdaterte deploy/fix-dokumenter fra backend (38 filer) |

Se **\`arkiv/README.md\`** i prosjektet for full oversikt over filer. For oppdatert prosedyre: Brukerhjelp i appen og Admin → Teknisk dokumentasjon.
`;

export default function AdminDocsPage() {
    const [technicalContent, setTechnicalContent] = useState('');
    const [activeTab, setActiveTab] = useState<'technical' | 'commands' | 'arkiv'>('commands');
    const [selectedCommand, setSelectedCommand] = useState<string>('ki-kollega');

    useEffect(() => {
        const loadContent = async () => {
            try {
                const data = await fetchAPI('/help/technical') as { content: string };
                setTechnicalContent(data.content || "# Ingen innhold\nKunne ikke finne teknisk dokumentasjon.");
            } catch (e) {
                setTechnicalContent("# Feil\nKunne ikke laste håndboken.");
                console.error(e);
            }
        };
        loadContent();
    }, []);

    const selectedDoc = COMMAND_DOCS.find(c => c.id === selectedCommand);

    return (
        <div className="min-h-screen bg-[#0B0F19] text-white p-8">
            <div className="max-w-6xl mx-auto">
                <Link href="/admin" className="flex items-center text-blue-400 hover:text-blue-300 mb-8 transition-colors">
                    <ArrowLeft className="w-4 h-4 mr-2" />
                    Tilbake til Admin
                </Link>

                <div className="glass-card rounded-2xl border border-white/10 overflow-hidden shadow-xl bg-[#131b2e]/80">
                    {/* Header */}
                    <div className="flex items-center gap-4 p-8 border-b border-white/10">
                        <div className="bg-blue-500/20 p-3 rounded-xl border border-blue-500/30">
                            <FileText className="w-8 h-8 text-blue-400" />
                        </div>
                        <div>
                            <h1 className="text-3xl font-bold text-white">Admin Håndbok</h1>
                            <p className="text-slate-400">Teknisk dokumentasjon og utvikler-kommandoer</p>
                        </div>
                    </div>

                    {/* Tabs */}
                    <div className="flex border-b border-white/10 bg-slate-900/30">
                        <button
                            onClick={() => setActiveTab('commands')}
                            className={`px-6 py-4 font-medium transition-colors flex items-center gap-2 ${activeTab === 'commands'
                                ? 'text-blue-400 border-b-2 border-blue-500 bg-blue-500/10'
                                : 'text-slate-400 hover:text-white hover:bg-white/5'
                                }`}
                        >
                            <Terminal className="w-4 h-4" />
                            Utvikler-kommandoer
                        </button>
                        <button
                            onClick={() => setActiveTab('technical')}
                            className={`px-6 py-4 font-medium transition-colors flex items-center gap-2 ${activeTab === 'technical'
                                ? 'text-blue-400 border-b-2 border-blue-500 bg-blue-500/10'
                                : 'text-slate-400 hover:text-white hover:bg-white/5'
                                }`}
                        >
                            <FileText className="w-4 h-4" />
                            Teknisk Dokumentasjon
                        </button>
                        <button
                            onClick={() => setActiveTab('arkiv')}
                            className={`px-6 py-4 font-medium transition-colors flex items-center gap-2 ${activeTab === 'arkiv'
                                ? 'text-blue-400 border-b-2 border-blue-500 bg-blue-500/10'
                                : 'text-slate-400 hover:text-white hover:bg-white/5'
                                }`}
                        >
                            <Archive className="w-4 h-4" />
                            Historisk dokumentasjon
                        </button>
                    </div>

                    {/* Content */}
                    {activeTab === 'commands' ? (
                        <div className="flex">
                            {/* Command Sidebar */}
                            <div className="w-72 border-r border-white/10 p-4 bg-slate-900/20">
                                <p className="text-xs uppercase tracking-wider text-slate-500 mb-3 px-2">Kommandoer</p>
                                <nav className="space-y-1">
                                    {COMMAND_DOCS.map(cmd => {
                                        const Icon = ICONS[cmd.icon] || Terminal;
                                        return (
                                            <button
                                                key={cmd.id}
                                                onClick={() => setSelectedCommand(cmd.id)}
                                                className={`w-full flex items-center gap-3 px-3 py-3 rounded-lg transition-all text-left ${selectedCommand === cmd.id
                                                    ? 'bg-blue-600 text-white shadow-lg shadow-blue-500/20'
                                                    : 'text-slate-300 hover:bg-white/10 hover:text-white'
                                                    }`}
                                            >
                                                <Icon className="w-4 h-4 flex-shrink-0" />
                                                <div className="min-w-0">
                                                    <div className="font-medium truncate">{cmd.title}</div>
                                                    <div className={`text-xs truncate ${selectedCommand === cmd.id ? 'text-blue-200' : 'text-slate-500'}`}>
                                                        {cmd.description}
                                                    </div>
                                                </div>
                                            </button>
                                        );
                                    })}
                                </nav>
                            </div>

                            {/* Command Content */}
                            <div className="flex-1 p-8 overflow-auto max-h-[70vh]">
                                {selectedDoc && (
                                    <div className="prose prose-invert max-w-none prose-headings:text-blue-200 prose-a:text-blue-400 hover:prose-a:text-blue-300 prose-code:text-blue-300 prose-code:bg-slate-900/50 prose-code:border prose-code:border-white/10 prose-pre:bg-slate-900/50 prose-pre:border prose-pre:border-white/10">
                                        <ReactMarkdown>{selectedDoc.content}</ReactMarkdown>
                                    </div>
                                )}
                            </div>
                        </div>
                    ) : activeTab === 'arkiv' ? (
                        <div className="p-8">
                            <div className="prose prose-invert max-w-none prose-headings:text-blue-200 prose-a:text-blue-400 hover:prose-a:text-blue-300 prose-code:text-blue-300 prose-code:bg-slate-900/50 prose-code:border prose-code:border-white/10 prose-table:text-slate-300">
                                <ReactMarkdown>{ARKIV_OVERVIEW_MD}</ReactMarkdown>
                            </div>
                        </div>
                    ) : (
                        <div className="p-8">
                            <div className="prose prose-invert max-w-none prose-headings:text-blue-200 prose-a:text-blue-400 hover:prose-a:text-blue-300 prose-code:text-blue-300 prose-code:bg-slate-900/50 prose-code:border prose-code:border-white/10">
                                <ReactMarkdown>{technicalContent}</ReactMarkdown>
                            </div>
                        </div>
                    )}
                </div>
            </div>
        </div>
    );
}
