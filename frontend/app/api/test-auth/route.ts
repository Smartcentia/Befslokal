import { NextResponse } from 'next/server';

export async function GET() {
    return NextResponse.json({
        timestamp: new Date().toISOString(),
        auth: "Supabase",
        env: {
            hasSupabaseUrl: !!process.env.NEXT_PUBLIC_SUPABASE_URL,
            hasSupabaseKey: !!process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY,
            apiUrl: process.env.NEXT_PUBLIC_API_URL,
            nodeEnv: process.env.NODE_ENV,
        },
        message: "Auth migrated to Supabase. Session available client-side via useAuth hook.",
    });
}
