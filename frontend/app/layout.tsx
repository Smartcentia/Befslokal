import type { Metadata } from "next";
import Script from "next/script";
import { Geist, Geist_Mono, Playfair_Display } from "next/font/google";
import "./globals.css";
import Header from "./components/ui/Header";
import Sidebar from "./components/ui/Sidebar";
import ChatWidget from "./components/features/ChatWidget";

const geistSans = Geist({
  variable: "--font-geist-sans",
  subsets: ["latin"],
});

const geistMono = Geist_Mono({
  variable: "--font-geist-mono",
  subsets: ["latin"],
});

const playfair = Playfair_Display({
  variable: "--font-playfair",
  subsets: ["latin"],
});

export const metadata: Metadata = {
  title: {
    template: '%s | BEFS',
    default: 'BEFS - Bufetat eiendomsforvaltningsystem',
  },
  description: "Eiendomssystem for norsk barnevern",
};

import { Providers } from "./providers";
import { ErrorBoundary } from "./components/ErrorBoundary";

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="no" suppressHydrationWarning data-theme="dark">
      <body
        className={`${geistSans.variable} ${geistMono.variable} ${playfair.variable} antialiased bg-background text-foreground`}
        suppressHydrationWarning
      >
        <Script src="/theme-init.js" strategy="beforeInteractive" />
        <Providers>
          <a href="#main-content" className="skip-link">
            Hopp til hovedinnhold
          </a>
          <div className="flex min-h-screen">
            {/* Sidebar: skjult på mobil, fast på desktop */}
            <div className="hidden lg:block">
              <Sidebar />
            </div>

            {/* Main Content Area */}
            <div className="flex min-h-0 flex-1 flex-col ml-0 lg:ml-72 transition-all duration-300">
              <Header />
              <ErrorBoundary componentName="Root Content">
                {/* pt-32: plass til fast header; pb-28: luft så flytende KI-knapp ikke skjuler bunninnhold */}
                <main id="main-content" className="min-h-0 flex-1 overflow-y-auto p-4 md:p-6 lg:p-8 pt-20 md:pt-24 lg:pt-32 pb-28">
                  {children}
                </main>
              </ErrorBoundary>
            </div>
          </div>
          <ChatWidget />
        </Providers>
      </body>
    </html>
  );
}
