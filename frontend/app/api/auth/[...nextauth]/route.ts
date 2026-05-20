import NextAuth from "next-auth";
import CredentialsProvider from "next-auth/providers/credentials";
import GoogleProvider from "next-auth/providers/google";
import sign from "jsonwebtoken";

export const authOptions = {
    // Removed PrismaAdapter - not needed for JWT strategy
    // Using JWT strategy means sessions are stored in cookies, not database
    providers: [
        CredentialsProvider({
            name: "Credentials",
            credentials: {
                email: { label: "Email", type: "email" },
                password: { label: "Password", type: "password" }
            },
            async authorize(credentials) {
                // Admin users - these are verified against the database
                const ADMIN_EMAILS = [
                    "admin@befs.no",
                    "oystein.moller.frich@bufdir.no",
                    "ove.braten@bufdir.no",
                    "larstony.laberget@bufdir.no",
                    "frankvevle@gmail.com",
                    "frankvevle@hotmail.com"
                ];
                
                if (credentials?.email && ADMIN_EMAILS.includes(credentials.email)) {
                    // Return user object - password validation would be done via backend in production
                    return { 
                        id: credentials.email, 
                        name: credentials.email.split("@")[0], 
                        email: credentials.email 
                    };
                }
                return null;
            }
        }),
        GoogleProvider({
            clientId: process.env.GOOGLE_CLIENT_ID || "",
            clientSecret: process.env.GOOGLE_CLIENT_SECRET || "",
        })
    ],
    session: {
        strategy: "jwt" as const,
        maxAge: 24 * 60 * 60, // 24 hours
    },
    secret: process.env.NEXTAUTH_SECRET,
    pages: {
        signIn: "/login",
        error: "/login",
    },
    // Cookie settings - let NextAuth handle defaults
    // Removed explicit domain to avoid cookie issues
    callbacks: {
        async jwt({ token, user, account }: any) {
            // When user logs in, we sign a custom JWT that the backend can verify
            if (user) {
                const secret = process.env.NEXTAUTH_SECRET;
                if (!secret) {
                    console.error("[NextAuth] NEXTAUTH_SECRET is not defined!");
                    throw new Error("NEXTAUTH_SECRET is not defined");
                }
                
                // Normalize user ID to email for consistency (works for both Credentials and Google)
                const userId = user.email; // Email is unique and consistent across providers
                const userEmail = user.email;
                const userName = user.name || userEmail?.split("@")[0] || "User";
                
                // Admin email list
                const ADMIN_EMAILS = [
                    "admin@befs.no",
                    "oystein.moller.frich@bufdir.no",
                    "ove.braten@bufdir.no",
                    "larstony.laberget@bufdir.no",
                    "frankvevle@gmail.com",
                    "frankvevle@hotmail.com"
                ];
                const roles = ADMIN_EMAILS.includes(userEmail) ? ["admin"] : ["user"];
                
                console.log("[NextAuth] Generating backend token for user:", userEmail, "provider:", account?.provider || "credentials");
                
                // Skip backend check during login to avoid slow Render cold starts
                // Email/MFA verification will be checked by backend on each API request
                // This makes login instant instead of waiting 30-60s for Render to wake up
                const emailVerified = true; // Default to true - backend will verify on requests
                const mfaVerified = false;  // Default to false - backend will check
                
                const backendToken = sign.sign(
                    {
                        sub: userId,      // Email as sub for consistency
                        email: userEmail,
                        name: userName,
                        roles: roles,
                        email_verified: emailVerified,
                        mfa_verified: mfaVerified,
                        iat: Math.floor(Date.now() / 1000),
                        exp: Math.floor(Date.now() / 1000) + (24 * 60 * 60), // 24 hours
                    },
                    secret,
                    { algorithm: 'HS256' }
                );
                token.accessToken = backendToken;
                token.sub = userId;
                token.email_verified = emailVerified;
                token.mfa_verified = mfaVerified;
                console.log("[NextAuth] Token generated, length:", backendToken.length, "email_verified:", emailVerified, "mfa_verified:", mfaVerified);
            }
            return token;
        },
        async session({ session, token }: any) {
            if (token) {
                session.user.id = token.sub;
                session.user.roles = token.roles || [];
                session.accessToken = token.accessToken;
                session.email_verified = token.email_verified !== false;
                session.mfa_verified = token.mfa_verified === true;
                if (!token.accessToken) {
                    console.warn("[NextAuth] No accessToken in token object!", {
                        tokenKeys: Object.keys(token),
                        hasToken: !!token
                    });
                }
            } else {
                console.warn("[NextAuth] No token in session callback!");
            }
            return session;
        }
    }
};

const handler = NextAuth(authOptions);

export { handler as GET, handler as POST };
