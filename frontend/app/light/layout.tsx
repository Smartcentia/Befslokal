import React from 'react';

export default function LightLayout({
    children,
}: {
    children: React.ReactNode;
}) {
    return (
        <div className="min-h-screen font-sans text-foreground bg-gradient-to-br from-[#FFF5F7] via-[#F3E8FF] to-[#E0F2FE]">
            {/* 
        Background Overlay for softness
        This creates the "blurry" feel from the reference image
      */}
            <div className="fixed inset-0 pointer-events-none bg-white/30 backdrop-blur-[100px] z-0" />

            {/* Main Content Container */}
            <div className="relative z-10 w-full max-w-[1600px] mx-auto p-6 md:p-12">
                {children}
            </div>
        </div>
    );
}
