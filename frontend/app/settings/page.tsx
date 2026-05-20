"use client";

import React, { useEffect, useState } from "react";
import { useAuth } from "@/hooks/useAuth";

export default function SettingsPage() {
    const { user, name: authName, email, role: authRole, loading } = useAuth();

    const [simulatedRole] = useState<string | null>(() => {
        if (typeof window !== "undefined") {
            return localStorage.getItem("simulate_role");
        }
        return null;
    });

    const realRole =
        authRole ||
        (user?.email === "admin@befs.no" || user?.email === "frankvevle@gmail.com"
            ? "admin"
            : "property_manager");
    const userRole = simulatedRole || realRole;

    const roleDisplay =
        userRole === "admin" || userRole === "ADMIN"
            ? "Administrator"
            : userRole === "property_manager" || userRole === "PROPERTY_MANAGER"
              ? "Eiendomsforvalter"
              : userRole === "janitor" || userRole === "JANITOR"
                ? "Vaktmester"
                : userRole === "tenant" || userRole === "TENANT"
                  ? "Leietaker"
                  : userRole === "regional_manager" || userRole === "REGIONAL_MANAGER"
                    ? "Regionansvarlig"
                    : String(userRole);

    const [profileName, setProfileName] = useState("");

    useEffect(() => {
        if (!loading && user) {
            setProfileName(authName || user.email?.split("@")[0] || "");
        }
    }, [loading, user, authName]);

    if (loading) {
        return (
            <div className="min-h-screen bg-slate-50 p-8">
                <h1 className="text-3xl font-bold text-slate-800 mb-8">Innstillinger</h1>
                <p className="text-slate-600">Laster bruker …</p>
            </div>
        );
    }

    if (!user) {
        return (
            <div className="min-h-screen bg-slate-50 p-8">
                <h1 className="text-3xl font-bold text-slate-800 mb-8">Innstillinger</h1>
                <p className="text-slate-600">Du er ikke innlogget.</p>
            </div>
        );
    }

    return (
        <div className="min-h-screen bg-slate-50 p-8">
            <h1 className="text-3xl font-bold text-slate-800 mb-8">Innstillinger</h1>

            <div className="grid grid-cols-1 md:grid-cols-2 gap-8">
                <div className="bg-white p-6 rounded-lg shadow-md border border-slate-200">
                    <h2 className="text-xl font-semibold mb-6 flex items-center gap-2">
                        <svg className="w-5 h-5 text-blue-500" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                            <path
                                strokeLinecap="round"
                                strokeLinejoin="round"
                                strokeWidth={2}
                                d="M16 7a4 4 0 11-8 0 4 4 0 018 0zM12 14a7 7 0 00-7 7h14a7 7 0 00-7-7z"
                            />
                        </svg>
                        Min profil
                    </h2>

                    <div className="space-y-4">
                        <div>
                            <label className="block text-sm font-medium text-slate-700 mb-1">Navn</label>
                            <input
                                type="text"
                                className="w-full px-3 py-2 border border-slate-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 text-slate-900"
                                value={profileName}
                                onChange={(e) => setProfileName(e.target.value)}
                                autoComplete="name"
                            />
                        </div>
                        <div>
                            <label className="block text-sm font-medium text-slate-700 mb-1">E-post</label>
                            <input
                                type="email"
                                readOnly
                                className="w-full px-3 py-2 border border-slate-200 rounded-md bg-slate-50 text-slate-700 cursor-not-allowed"
                                value={email ?? ""}
                            />
                            <p className="text-xs text-slate-500 mt-1">Hentet fra innlogging.</p>
                        </div>
                        <div>
                            <label className="block text-sm font-medium text-slate-700 mb-1">Rolle</label>
                            <p className="text-slate-900">
                                {roleDisplay}
                                {simulatedRole ? (
                                    <span className="ml-2 text-amber-600 text-sm" title="Simulert rolle">
                                        (simulering)
                                    </span>
                                ) : null}
                            </p>
                        </div>
                    </div>
                </div>

                <div className="bg-white p-6 rounded-lg shadow-md border border-slate-200">
                    <h2 className="text-xl font-semibold mb-6 flex items-center gap-2">
                        <svg className="w-5 h-5 text-purple-500" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                            <path
                                strokeLinecap="round"
                                strokeLinejoin="round"
                                strokeWidth={2}
                                d="M10.325 4.317c.426-1.756 2.924-1.756 3.35 0a1.724 1.724 0 002.573 1.066c1.543-.94 3.31.826 2.37 2.37a1.724 1.724 0 001.065 2.572c1.756.426 1.756 2.924 0 3.35a1.724 1.724 0 00-1.066 2.573c.94 1.543-.826 3.31-2.37 2.37a1.724 1.724 0 00-2.572 1.065c-.426 1.756-2.924 1.756-3.35 0a1.724 1.724 0 00-2.573-1.066c-1.543.94-3.31-.826-2.37-2.37a1.724 1.724 0 00-1.065-2.572c-1.756-.426-1.756-2.924 0-3.35a1.724 1.724 0 001.066-2.573c-.94-1.543.826-3.31 2.37-2.37.996.608 2.296.07 2.572-1.065z"
                            />
                            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 12a3 3 0 11-6 0 3 3 0 016 0z" />
                        </svg>
                        Systeminnstillinger
                    </h2>

                    <div className="space-y-4">
                        <div className="flex items-center justify-between">
                            <span className="text-slate-700">Mørk modus</span>
                            <div className="w-11 h-6 bg-slate-200 rounded-full relative cursor-pointer">
                                <div className="absolute left-1 top-1 w-4 h-4 bg-white rounded-full shadow-sm transition-transform"></div>
                            </div>
                        </div>
                        <div className="flex items-center justify-between">
                            <span className="text-slate-700">E-postvarsling ved avvik</span>
                            <div className="w-11 h-6 bg-green-500 rounded-full relative cursor-pointer">
                                <div className="absolute right-1 top-1 w-4 h-4 bg-white rounded-full shadow-sm transition-transform"></div>
                            </div>
                        </div>
                        <div className="flex items-center justify-between">
                            <span className="text-slate-700">Lyd for varsler</span>
                            <div className="w-11 h-6 bg-green-500 rounded-full relative cursor-pointer">
                                <div className="absolute right-1 top-1 w-4 h-4 bg-white rounded-full shadow-sm transition-transform"></div>
                            </div>
                        </div>
                    </div>

                    <div className="mt-8 pt-6 border-t border-slate-100">
                        <h3 className="text-sm font-bold text-slate-500 uppercase tracking-wide mb-3">Systemstatus</h3>
                        <div className="text-sm text-slate-600 flex justify-between">
                            <span>Backend API:</span>
                            <span className="text-green-600 font-medium">Connected (v1.0.0)</span>
                        </div>
                        <div className="text-sm text-slate-600 flex justify-between mt-1">
                            <span>Database:</span>
                            <span className="text-green-600 font-medium">Cloud PostgreSQL</span>
                        </div>
                    </div>
                </div>
            </div>

            <div className="mt-8 flex justify-end">
                <button
                    type="button"
                    className="bg-blue-600 text-white px-6 py-2 rounded-lg font-medium hover:bg-blue-700 shadow-md transition-all"
                >
                    Lagre endringer
                </button>
            </div>
        </div>
    );
}
