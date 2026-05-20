"use client";

import { useState, useEffect } from 'react';
import { getUsers } from '@/lib/api/userManagementApi';
import type { UserProfile } from '@/lib/api/userManagementApi';

export default function ImpersonationPage() {
    const [users, setUsers] = useState<UserProfile[]>([]);
    const [loading, setLoading] = useState(true);
    const [selectedEmail, setSelectedEmail] = useState<string>('');
    const [filterRole, setFilterRole] = useState<string>('all');
    const [filterRegion, setFilterRegion] = useState<string>('all');

    useEffect(() => {
        fetchUsers();

        // Check if currently impersonating
        const currentImpersonation = localStorage.getItem('impersonate_email');
        if (currentImpersonation) {
            setSelectedEmail(currentImpersonation);
        }
    }, []);

    const fetchUsers = async () => {
        try {
            setLoading(true);
            const data = await getUsers();
            setUsers(data);
        } catch (error) {
            console.error('Failed to fetch users:', error);
            alert('Kunne ikke hente brukere. Sjekk at du er logget inn som admin.');
        } finally {
            setLoading(false);
        }
    };

    const handleImpersonate = (email: string) => {
        localStorage.setItem('impersonate_email', email);
        setSelectedEmail(email);
        alert(`Du simulerer nå: ${email}\n\nAlle API-kall vil nå kjøres som denne brukeren.\n\nGå til HMS Kalender eller annen side for å teste.`);
    };

    const handleStopImpersonation = () => {
        localStorage.removeItem('impersonate_email');
        setSelectedEmail('');
        alert('Impersonering stoppet. Du bruker nå din egen bruker.');
    };

    const filteredUsers = users.filter(user => {
        if (filterRole !== 'all' && user.role !== filterRole) return false;
        if (filterRegion !== 'all' && user.region !== filterRegion) return false;
        return true;
    });

    const uniqueRoles = Array.from(new Set(users.map(u => u.role)));
    const uniqueRegions = Array.from(new Set(users.map(u => u.region).filter(Boolean)));

    const getRoleBadgeColor = (role: string) => {
        switch (role.toUpperCase()) {
            case 'ADMIN':              return 'border border-purple-200 bg-purple-100 text-purple-800 dark:border-purple-500/30 dark:bg-purple-500/15 dark:text-purple-300';
            case 'NASJONAL_LEDER':     return 'border border-violet-200 bg-violet-100 text-violet-800 dark:border-violet-500/30 dark:bg-violet-500/15 dark:text-violet-300';
            case 'REGIONAL_MANAGER':   return 'border border-blue-200 bg-blue-100 text-blue-800 dark:border-blue-500/30 dark:bg-blue-500/15 dark:text-blue-300';
            case 'OKONOMIANSVARLIG':   return 'border border-emerald-200 bg-emerald-100 text-emerald-800 dark:border-emerald-500/30 dark:bg-emerald-500/15 dark:text-emerald-300';
            case 'PROPERTY_MANAGER':   return 'border border-green-200 bg-green-100 text-green-800 dark:border-green-500/30 dark:bg-green-500/15 dark:text-green-300';
            case 'KONTRAKTSFORVALTER': return 'border border-teal-200 bg-teal-100 text-teal-800 dark:border-teal-500/30 dark:bg-teal-500/15 dark:text-teal-300';
            case 'FDVU_KOORDINATOR':   return 'border border-cyan-200 bg-cyan-100 text-cyan-800 dark:border-cyan-500/30 dark:bg-cyan-500/15 dark:text-cyan-300';
            case 'DRIFTSANSVARLIG':    return 'border border-sky-200 bg-sky-100 text-sky-800 dark:border-sky-500/30 dark:bg-sky-500/15 dark:text-sky-300';
            case 'JANITOR':            return 'border border-orange-200 bg-orange-100 text-orange-800 dark:border-orange-500/30 dark:bg-orange-500/15 dark:text-orange-300';
            case 'HMS_ANSVARLIG':      return 'border border-red-200 bg-red-100 text-red-800 dark:border-red-500/30 dark:bg-red-500/15 dark:text-red-300';
            case 'TENANT':             return 'border border-gray-200 bg-gray-100 text-gray-700 dark:border-gray-500/30 dark:bg-gray-500/15 dark:text-gray-300';
            case 'REVISOR':            return 'border border-slate-200 bg-slate-100 text-slate-700 dark:border-slate-500/30 dark:bg-slate-500/15 dark:text-slate-300';
            default:                   return 'border border-border bg-surface text-foreground';
        }
    };

    const getRoleLabel = (role: string) => {
        const labels: Record<string, string> = {
            ADMIN: 'Administrator', NASJONAL_LEDER: 'Nasjonal leder',
            REGIONAL_MANAGER: 'Regionleder', OKONOMIANSVARLIG: 'Økonomiansvarlig',
            PROPERTY_MANAGER: 'Eiendomsforvalter', KONTRAKTSFORVALTER: 'Kontraktsforvalter',
            FDVU_KOORDINATOR: 'FDVU-koordinator', DRIFTSANSVARLIG: 'Driftsansvarlig',
            JANITOR: 'Vaktmester', HMS_ANSVARLIG: 'HMS-ansvarlig',
            TENANT: 'Leietaker', REVISOR: 'Revisor',
        };
        return labels[role.toUpperCase()] ?? role;
    };

    return (
        <div className="min-h-screen bg-background p-6">
            <div className="max-w-7xl mx-auto">
                <div className="rounded-lg border border-border bg-card p-6 shadow-sm mb-6">
                    <div className="flex justify-between items-center mb-6">
                        <div>
                            <h1 className="text-3xl font-bold text-foreground">Bruker Impersonering</h1>
                            <p className="text-muted mt-1">
                                Velg en bruker for å teste systemet med deres rettigheter
                            </p>
                        </div>
                        {selectedEmail && (
                            <button
                                onClick={handleStopImpersonation}
                                className="rounded-md bg-destructive px-4 py-2 text-destructive-foreground transition-colors hover:bg-destructive/90"
                            >
                                Stopp Impersonering
                            </button>
                        )}
                    </div>

                    {selectedEmail && (
                        <div className="mb-6 rounded border-l-4 border-warning bg-warning/10 p-4">
                            <div className="flex items-center">
                                <div className="shrink-0">
                                    <svg className="h-5 w-5 text-warning" viewBox="0 0 20 20" fill="currentColor">
                                        <path fillRule="evenodd" d="M8.257 3.099c.765-1.36 2.722-1.36 3.486 0l5.58 9.92c.75 1.334-.213 2.98-1.742 2.98H4.42c-1.53 0-2.493-1.646-1.743-2.98l5.58-9.92zM11 13a1 1 0 11-2 0 1 1 0 012 0zm-1-8a1 1 0 00-1 1v3a1 1 0 002 0V6a1 1 0 00-1-1z" clipRule="evenodd" />
                                    </svg>
                                </div>
                                <div className="ml-3">
                                    <p className="text-sm font-medium text-foreground">
                                        Du impersonerer: <strong>{selectedEmail}</strong>
                                    </p>
                                </div>
                            </div>
                        </div>
                    )}


                    <div className="flex gap-4 mb-6">
                        <div className="flex-1">
                            <label htmlFor="filter-role" className="block text-sm font-medium text-foreground mb-1">
                                Rolle
                            </label>
                            <select
                                id="filter-role"
                                value={filterRole}
                                onChange={(e) => setFilterRole(e.target.value)}
                                className="enterprise-input"
                            >
                                <option value="all">Alle roller</option>
                                {uniqueRoles.map(role => (
                                    <option key={role} value={role}>{getRoleLabel(role)}</option>
                                ))}
                            </select>
                        </div>

                        <div className="flex-1">
                            <label htmlFor="filter-region" className="block text-sm font-medium text-foreground mb-1">
                                Region
                            </label>
                            <select
                                id="filter-region"
                                value={filterRegion}
                                onChange={(e) => setFilterRegion(e.target.value)}
                                className="enterprise-input"
                            >
                                <option value="all">Alle regioner</option>
                                {uniqueRegions.map(region => (
                                    <option key={region} value={region}>{region}</option>
                                ))}
                            </select>
                        </div>
                    </div>

                    <div className="mb-6 grid grid-cols-4 gap-4">
                        <div className="rounded-lg border border-purple-200 bg-purple-50 p-4 dark:border-purple-500/25 dark:bg-purple-500/10">
                            <div className="text-2xl font-bold text-purple-900 dark:text-purple-200">
                                {users.filter(u => u.role?.toLowerCase() === 'admin').length}
                            </div>
                            <div className="text-sm text-purple-700 dark:text-purple-300">Bufdir Admins</div>
                        </div>
                        <div className="rounded-lg border border-blue-200 bg-blue-50 p-4 dark:border-blue-500/25 dark:bg-blue-500/10">
                            <div className="text-2xl font-bold text-blue-900 dark:text-blue-200">
                                {users.filter(u => u.role?.toLowerCase() === 'regional_manager').length}
                            </div>
                            <div className="text-sm text-blue-700 dark:text-blue-300">Regionledere</div>
                        </div>
                        <div className="rounded-lg border border-emerald-200 bg-emerald-50 p-4 dark:border-emerald-500/25 dark:bg-emerald-500/10">
                            <div className="text-2xl font-bold text-emerald-900 dark:text-emerald-200">
                                {users.filter(u => u.role?.toLowerCase() === 'property_manager').length}
                            </div>
                            <div className="text-sm text-emerald-700 dark:text-emerald-300">Eiendomsforvaltere</div>
                        </div>
                        <div className="rounded-lg border border-orange-200 bg-orange-50 p-4 dark:border-orange-500/25 dark:bg-orange-500/10">
                            <div className="text-2xl font-bold text-orange-900 dark:text-orange-200">
                                {users.filter(u => ['janitor', 'tenant'].includes(u.role?.toLowerCase() || '')).length}
                            </div>
                            <div className="text-sm text-orange-700 dark:text-orange-300">Vaktmestre</div>
                        </div>
                    </div>
                </div>

                <div className="overflow-hidden rounded-lg border border-border bg-card shadow-sm">
                    {loading ? (
                        <div className="flex items-center justify-center p-12">
                            <div className="text-muted">Laster brukere...</div>
                        </div>
                    ) : (
                        <table className="min-w-full divide-y divide-border">
                            <thead className="bg-surface/80">
                                <tr>
                                    <th className="px-6 py-3 text-left text-xs font-medium uppercase tracking-wider text-muted">
                                        Navn
                                    </th>
                                    <th className="px-6 py-3 text-left text-xs font-medium uppercase tracking-wider text-muted">
                                        E-post
                                    </th>
                                    <th className="px-6 py-3 text-left text-xs font-medium uppercase tracking-wider text-muted">
                                        Rolle
                                    </th>
                                    <th className="px-6 py-3 text-left text-xs font-medium uppercase tracking-wider text-muted">
                                        Region
                                    </th>
                                    <th className="px-6 py-3 text-right text-xs font-medium uppercase tracking-wider text-muted">
                                        Handling
                                    </th>
                                </tr>
                            </thead>
                            <tbody className="divide-y divide-border bg-card">
                                {filteredUsers.map(user => (
                                    <tr key={user.user_id} className={selectedEmail === user.email ? 'bg-warning/10' : 'hover:bg-surface/50'}>
                                        <td className="px-6 py-4 whitespace-nowrap">
                                            <div className="text-sm font-medium text-foreground">{user.name || '-'}</div>
                                        </td>
                                        <td className="px-6 py-4 whitespace-nowrap">
                                            <div className="text-sm text-muted">{user.email}</div>
                                        </td>
                                        <td className="px-6 py-4 whitespace-nowrap">
                                            <span className={`inline-flex rounded-full px-2 text-xs leading-5 font-semibold ${getRoleBadgeColor(user.role)}`}>
                                                {getRoleLabel(user.role)}
                                            </span>
                                        </td>
                                        <td className="px-6 py-4 whitespace-nowrap text-sm text-muted">
                                            {user.region || '-'}
                                        </td>
                                        <td className="px-6 py-4 whitespace-nowrap text-right text-sm font-medium">
                                            {selectedEmail === user.email ? (
                                                <span className="font-semibold text-warning">Aktiv</span>
                                            ) : (
                                                <button
                                                    onClick={() => handleImpersonate(user.email)}
                                                    className="text-primary hover:text-primary/80"
                                                >
                                                    Simuler
                                                </button>
                                            )}
                                        </td>
                                    </tr>
                                ))}
                            </tbody>
                        </table>
                    )}
                </div>

                <div className="mt-6 rounded border-l-4 border-primary bg-primary/5 p-4">
                    <div className="flex">
                        <div className="shrink-0">
                            <svg className="h-5 w-5 text-primary" viewBox="0 0 20 20" fill="currentColor">
                                <path fillRule="evenodd" d="M18 10a8 8 0 11-16 0 8 8 0 0116 0zm-7-4a1 1 0 11-2 0 1 1 0 012 0zM9 9a1 1 0 000 2v3a1 1 0 001 1h1a1 1 0 100-2v-3a1 1 0 00-1-1H9z" clipRule="evenodd" />
                            </svg>
                        </div>
                        <div className="ml-3">
                            <h3 className="text-sm font-medium text-foreground">Slik bruker du impersonering:</h3>
                            <div className="mt-2 text-sm text-muted">
                                <ol className="list-decimal list-inside space-y-1">
                                    <li>Klikk &quot;Simuler&quot; på brukeren du vil teste som</li>
                                    <li>Gå til HMS Kalender eller andre sider for å teste funksjonalitet</li>
                                    <li>API-kall vil nå kjøres med den valgte brukerens rettigheter</li>
                                    <li>Klikk &quot;Stopp Impersonering&quot; for å gå tilbake til din egen bruker</li>
                                </ol>
                            </div>
                        </div>
                    </div>
                </div>
            </div>
        </div>
    );
}
