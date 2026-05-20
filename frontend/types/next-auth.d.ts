/**
 * NextAuth Session type extension (Fix 7 - CODE_REVIEW_30-01).
 * Use session.accessToken instead of (session as any).accessToken.
 */
import "next-auth";

declare module "next-auth" {
  interface Session {
    accessToken?: string;
    user: {
      id: string;
      email: string;
      name?: string | null;
      image?: string | null;
      isAdmin?: boolean;
      roles?: string[];
      assigned_properties?: string[];
    };
  }
}

