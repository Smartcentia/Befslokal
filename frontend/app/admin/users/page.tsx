'use client';

import { useEffect, useState } from 'react';
import {
  getUsers,
  getUser,
  createUser,
  updateUser,
  deleteUser,
  type UserProfile,
  type UserCreateInput,
} from '@/lib/api/userManagementApi';
import { propertyService, type Property } from '@/lib/domains/core/propertyService';
import { Button } from '@/components/ui/button';
import Link from 'next/link';

const ROLES = [
  // Strategisk / ledelse
  { value: 'ADMIN',              label: 'Administrator (Bufdir)',     group: 'Ledelse' },
  { value: 'NASJONAL_LEDER',     label: 'Nasjonal leder',            group: 'Ledelse' },
  { value: 'REGIONAL_MANAGER',   label: 'Regionleder',               group: 'Ledelse' },
  // Økonomi
  { value: 'OKONOMIANSVARLIG',   label: 'Økonomiansvarlig',          group: 'Økonomi' },
  // Eiendomsforvaltning
  { value: 'PROPERTY_MANAGER',   label: 'Eiendomsforvalter',         group: 'Eiendom' },
  { value: 'KONTRAKTSFORVALTER', label: 'Kontraktsforvalter',        group: 'Eiendom' },
  // FDVU / Drift
  { value: 'FDVU_KOORDINATOR',   label: 'FDVU-koordinator',          group: 'FDVU' },
  { value: 'DRIFTSANSVARLIG',    label: 'Driftsansvarlig',           group: 'FDVU' },
  { value: 'JANITOR',            label: 'Vaktmester',                group: 'FDVU' },
  // HMS
  { value: 'HMS_ANSVARLIG',      label: 'HMS-ansvarlig',             group: 'HMS' },
  // Ekstern / read-only
  { value: 'TENANT',             label: 'Leietaker',                 group: 'Ekstern' },
  { value: 'REVISOR',            label: 'Revisor (kun les)',         group: 'Ekstern' },
] as const;

const ROLE_VALUES = ROLES.map((r) => r.value);

/** API og <select> bruker ALL_CAPS; eldre skjema brukte små bokstaver — normaliser for gyldig kontrollert felt. */
function normalizeRole(role: string | undefined | null): string {
  if (!role) return 'PROPERTY_MANAGER';
  const trimmed = String(role).trim();
  const upper = trimmed.toUpperCase();
  if (ROLE_VALUES.includes(upper as (typeof ROLE_VALUES)[number])) return upper;
  const legacy: Record<string, string> = {
    admin: 'ADMIN',
    nasjonal_leder: 'NASJONAL_LEDER',
    regional_manager: 'REGIONAL_MANAGER',
    okonomiansvarlig: 'OKONOMIANSVARLIG',
    property_manager: 'PROPERTY_MANAGER',
    kontraktsforvalter: 'KONTRAKTSFORVALTER',
    fdvu_koordinator: 'FDVU_KOORDINATOR',
    driftsansvarlig: 'DRIFTSANSVARLIG',
    janitor: 'JANITOR',
    hms_ansvarlig: 'HMS_ANSVARLIG',
    tenant: 'TENANT',
    revisor: 'REVISOR',
  };
  return legacy[trimmed.toLowerCase()] ?? 'PROPERTY_MANAGER';
}

function getRoleLabel(role: string) {
  return ROLES.find((r) => r.value === role.toUpperCase())?.label ?? role;
}

function getRoleBadgeClass(role: string) {
  const upperRole = role.toUpperCase();
  switch (upperRole) {
    case 'ADMIN':             return 'bg-purple-100 text-purple-800 dark:bg-purple-950/40 dark:text-purple-300';
    case 'NASJONAL_LEDER':    return 'bg-violet-100 text-violet-800 dark:bg-violet-950/40 dark:text-violet-300';
    case 'REGIONAL_MANAGER':  return 'bg-blue-100 text-blue-800 dark:bg-blue-950/40 dark:text-blue-300';
    case 'OKONOMIANSVARLIG':  return 'bg-emerald-100 text-emerald-800 dark:bg-emerald-950/40 dark:text-emerald-300';
    case 'PROPERTY_MANAGER':  return 'bg-green-100 text-green-800 dark:bg-green-950/40 dark:text-green-300';
    case 'KONTRAKTSFORVALTER':return 'bg-teal-100 text-teal-800 dark:bg-teal-950/40 dark:text-teal-300';
    case 'FDVU_KOORDINATOR':  return 'bg-cyan-100 text-cyan-800 dark:bg-cyan-950/40 dark:text-cyan-300';
    case 'DRIFTSANSVARLIG':   return 'bg-sky-100 text-sky-800 dark:bg-sky-950/40 dark:text-sky-300';
    case 'JANITOR':           return 'bg-orange-100 text-orange-800 dark:bg-orange-950/40 dark:text-orange-300';
    case 'HMS_ANSVARLIG':     return 'bg-red-100 text-red-800 dark:bg-red-950/40 dark:text-red-300';
    case 'TENANT':            return 'bg-gray-100 text-gray-700 dark:bg-gray-800 dark:text-gray-300';
    case 'REVISOR':           return 'bg-slate-100 text-slate-700 dark:bg-slate-800 dark:text-slate-300';
    default:                  return 'bg-gray-100 text-gray-800';
  }
}

export default function AdminUsersPage() {
  const [users, setUsers] = useState<UserProfile[]>([]);
  const [properties, setProperties] = useState<Property[]>([]);
  const [loading, setLoading] = useState(true);
  const [impersonating, setImpersonating] = useState<string | null>(null);
  const [message, setMessage] = useState<{ type: 'success' | 'error'; text: string } | null>(null);
  const [modal, setModal] = useState<'add' | 'edit' | 'delete' | null>(null);
  const [editingUser, setEditingUser] = useState<UserProfile | null>(null);
  const [formData, setFormData] = useState<UserCreateInput>({
    email: '',
    name: '',
    role: 'PROPERTY_MANAGER',
    region: '',
    property_ids: [],
  });
  const [submitting, setSubmitting] = useState(false);

  useEffect(() => {
    if (typeof window !== 'undefined') {
      setImpersonating(localStorage.getItem('impersonate_email'));
    }
    loadUsers();
    loadProperties();
  }, []);

  const loadUsers = async () => {
    try {
      const data = await getUsers();
      setUsers(data);
    } catch (e) {
      console.error('Failed to load users', e);
      setMessage({ type: 'error', text: 'Kunne ikke laste brukere' });
    } finally {
      setLoading(false);
    }
  };

  const loadProperties = async () => {
    try {
      const data = await propertyService.getAll(0, 500);
      setProperties(data);
    } catch (e) {
      console.error('Failed to load properties', e);
    }
  };

  const handleSimulate = (email: string) => {
    if (typeof window !== 'undefined') {
      localStorage.setItem('impersonate_email', email);
      setImpersonating(email);
      window.location.href = '/dashboard';
    }
  };

  const handleStop = () => {
    if (typeof window !== 'undefined') {
      localStorage.removeItem('impersonate_email');
      setImpersonating(null);
      window.location.reload();
    }
  };

  const openAddModal = () => {
    setFormData({
      email: '',
      name: '',
      role: 'PROPERTY_MANAGER',
      region: '',
      property_ids: [],
    });
    setModal('add');
  };

  const openEditModal = async (user: UserProfile) => {
    setEditingUser(user);
    try {
      const detail = await getUser(user.user_id);
      setFormData({
        email: detail.email ?? user.email ?? '',
        name: detail.name ?? '',
        role: normalizeRole(detail.role),
        region: detail.region ?? '',
        property_ids: detail.property_ids ?? [],
      });
      setModal('edit');
    } catch (e) {
      console.error('Failed to load user', e);
      setMessage({ type: 'error', text: 'Kunne ikke laste bruker' });
    }
  };

  const openDeleteModal = (user: UserProfile) => {
    setEditingUser(user);
    setModal('delete');
  };

  const closeModal = () => {
    setModal(null);
    setEditingUser(null);
    setSubmitting(false);
  };

  const handleCreate = async () => {
    if (!formData.email?.trim()) {
      setMessage({ type: 'error', text: 'E-post er påkrevd' });
      return;
    }
    setSubmitting(true);
    try {
      await createUser({
        ...formData,
        role: normalizeRole(formData.role),
      });
      setMessage({ type: 'success', text: 'Bruker opprettet' });
      closeModal();
      loadUsers();
    } catch (e) {
      setMessage({ type: 'error', text: e instanceof Error ? e.message : 'Kunne ikke opprette bruker' });
    } finally {
      setSubmitting(false);
    }
  };

  const handleUpdate = async () => {
    if (!editingUser) return;
    setSubmitting(true);
    try {
      await updateUser(editingUser.user_id, {
        name: formData.name,
        role: normalizeRole(formData.role),
        region: formData.region,
        property_ids: formData.property_ids,
      });
      setMessage({ type: 'success', text: 'Bruker oppdatert' });
      closeModal();
      loadUsers();
    } catch (e) {
      setMessage({ type: 'error', text: e instanceof Error ? e.message : 'Kunne ikke oppdatere bruker' });
    } finally {
      setSubmitting(false);
    }
  };

  const handleDelete = async () => {
    if (!editingUser) return;
    setSubmitting(true);
    try {
      await deleteUser(editingUser.user_id);
      setMessage({ type: 'success', text: 'Bruker deaktivert' });
      closeModal();
      loadUsers();
    } catch (e) {
      setMessage({ type: 'error', text: e instanceof Error ? e.message : 'Kunne ikke deaktivere bruker' });
    } finally {
      setSubmitting(false);
    }
  };

  const toggleProperty = (propertyId: string) => {
    setFormData((prev) => {
      const ids = prev.property_ids ?? [];
      const next = ids.includes(propertyId) ? ids.filter((id) => id !== propertyId) : [...ids, propertyId];
      return { ...prev, property_ids: next };
    });
  };

  const uniqueRegions = Array.from(new Set(properties.map((p) => p.region).filter(Boolean))) as string[];

  const roleNorm = normalizeRole(formData.role);
  const showRegion = roleNorm === 'REGIONAL_MANAGER';
  const showProperties = roleNorm === 'PROPERTY_MANAGER' || roleNorm === 'JANITOR';

  return (
    <div className="p-8 bg-slate-50 min-h-screen">
      <div className="max-w-6xl mx-auto">
        <div className="flex justify-between items-center mb-6">
          <h1 className="text-3xl font-bold text-slate-800">Brukeradministrasjon</h1>
          <div className="flex gap-2">
            <Link href="/admin">
              <Button variant="outline">Tilbake til Admin</Button>
            </Link>
            <Button onClick={openAddModal}>Legg til bruker</Button>
          </div>
        </div>

        {message && (
          <div
            className={`mb-6 p-4 rounded-lg ${
              message.type === 'success' ? 'bg-green-100 text-green-800' : 'bg-red-100 text-red-800'
            }`}
          >
            {message.text}
            <button
              className="ml-4 underline"
              onClick={() => setMessage(null)}
            >
              Lukk
            </button>
          </div>
        )}

        {impersonating && (
          <div className="bg-amber-100 border-l-4 border-amber-500 text-amber-900 p-4 mb-8 flex justify-between items-center rounded shadow-sm">
            <div>
              <p className="font-bold">Du simulerer nå: {impersonating}</p>
              <p className="text-sm">Alle handlinger du gjør nå vil bli utført som denne brukeren.</p>
            </div>
            <Button onClick={handleStop} variant="destructive">
              Stopp Simulering
            </Button>
          </div>
        )}

        <div className="bg-white rounded-lg shadow border border-slate-200 overflow-hidden">
          <table className="w-full text-left">
            <thead className="bg-slate-100 border-b border-slate-200">
              <tr>
                <th className="p-4 font-semibold text-slate-700">Navn</th>
                <th className="p-4 font-semibold text-slate-700">E-post</th>
                <th className="p-4 font-semibold text-slate-700">Rolle</th>
                <th className="p-4 font-semibold text-slate-700">Region</th>
                <th className="p-4 font-semibold text-slate-700">Handling</th>
              </tr>
            </thead>
            <tbody>
              {users.map((user) => (
                <tr key={user.user_id} className="border-b border-slate-100 hover:bg-slate-50 transition-colors">
                  <td className="p-4 font-medium text-slate-900">{user.name || '-'}</td>
                  <td className="p-4 text-slate-600 font-mono text-sm">{user.email}</td>
                  <td className="p-4">
                    <span className={`px-2 py-1 rounded-full text-xs font-semibold ${getRoleBadgeClass(user.role)}`}>
                      {getRoleLabel(user.role)}
                    </span>
                  </td>
                  <td className="p-4 text-slate-600">{user.region || '-'}</td>
                  <td className="p-4 flex gap-2">
                    <Button variant="outline" size="sm" onClick={() => openEditModal(user)}>
                      Rediger
                    </Button>
                    <Button variant="destructive" size="sm" onClick={() => openDeleteModal(user)}>
                      Deaktiver
                    </Button>
                    {impersonating === user.email ? (
                      <span className="text-green-600 font-bold text-sm py-1">Aktiv</span>
                    ) : (
                      <Button variant="secondary" size="sm" onClick={() => handleSimulate(user.email)}>
                        Simuler
                      </Button>
                    )}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
          {loading && <div className="p-8 text-center text-slate-500">Laster brukere...</div>}
          {!loading && users.length === 0 && (
            <div className="p-8 text-center text-slate-500">Ingen brukere funnet.</div>
          )}
        </div>
      </div>

      {/* Add/Edit Modal */}
      {(modal === 'add' || modal === 'edit') && (
        <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4">
          <div className="bg-white rounded-lg shadow-xl max-w-lg w-full max-h-[90vh] overflow-y-auto">
            <div className="p-6">
              <h2 className="text-xl font-bold mb-6">{modal === 'add' ? 'Legg til bruker' : 'Rediger bruker'}</h2>

              {modal === 'add' && (
                <div className="mb-4">
                  <label className="block text-sm font-medium text-slate-700 mb-1">E-post *</label>
                  <input
                    type="email"
                    value={formData.email}
                    onChange={(e) => setFormData((p) => ({ ...p, email: e.target.value }))}
                    className="w-full border border-slate-300 rounded-md px-3 py-2 bg-white text-slate-800 placeholder:text-slate-400"
                    placeholder="bruker@example.com"
                  />
                </div>
              )}

              <div className="mb-4">
                <label className="block text-sm font-medium text-slate-700 mb-1">Navn</label>
                <input
                  type="text"
                  value={formData.name ?? ''}
                  onChange={(e) => setFormData((p) => ({ ...p, name: e.target.value }))}
                  className="w-full border border-slate-300 rounded-md px-3 py-2 bg-white text-slate-800 placeholder:text-slate-400"
                  placeholder="Fornavn Etternavn"
                />
              </div>

              <div className="mb-4">
                <label className="block text-sm font-medium text-slate-700 mb-1">Rolle</label>
                <select
                  value={roleNorm}
                  title="Velg brukerrolle"
                  onChange={(e) =>
                    setFormData((p) => ({ ...p, role: normalizeRole(e.target.value) }))
                  }
                  className="w-full border border-slate-300 rounded-md px-3 py-2 bg-white text-slate-800"
                >
                  {ROLES.map((r) => (
                    <option key={r.value} value={r.value}>
                      {r.label}
                    </option>
                  ))}
                </select>
              </div>

              {showRegion && (
                <div className="mb-4">
                  <label className="block text-sm font-medium text-slate-700 mb-1">Region</label>
                  <input
                    type="text"
                    value={formData.region ?? ''}
                    onChange={(e) => setFormData((p) => ({ ...p, region: e.target.value }))}
                    className="w-full border border-slate-300 rounded-md px-3 py-2 bg-white text-slate-800 placeholder:text-slate-400"
                    placeholder="f.eks. 02 - Øst"
                    list="regions-list"
                  />
                  <datalist id="regions-list">
                    {uniqueRegions.map((r) => (
                      <option key={r} value={r} />
                    ))}
                  </datalist>
                </div>
              )}

              {showProperties && (
                <div className="mb-4">
                  <label className="block text-sm font-medium text-slate-700 mb-1">Eiendommer</label>
                  <div className="border border-slate-300 rounded-md p-3 max-h-40 overflow-y-auto space-y-2">
                    {properties.length === 0 ? (
                      <p className="text-slate-500 text-sm">Ingen eiendommer tilgjengelig</p>
                    ) : (
                      properties.map((prop) => (
                        <label key={prop.property_id} className="flex items-center gap-2 cursor-pointer">
                          <input
                            type="checkbox"
                            checked={(formData.property_ids ?? []).includes(prop.property_id)}
                            onChange={() => toggleProperty(prop.property_id)}
                          />
                          <span className="text-sm">
                            {prop.name || prop.address || prop.property_id}
                          </span>
                        </label>
                      ))
                    )}
                  </div>
                </div>
              )}

              <div className="flex justify-end gap-2 mt-6">
                <Button variant="outline" onClick={closeModal} disabled={submitting}>
                  Avbryt
                </Button>
                {modal === 'add' ? (
                  <Button onClick={handleCreate} disabled={submitting}>
                    {submitting ? 'Oppretter...' : 'Opprett'}
                  </Button>
                ) : (
                  <Button onClick={handleUpdate} disabled={submitting}>
                    {submitting ? 'Lagrer...' : 'Lagre'}
                  </Button>
                )}
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Delete confirmation */}
      {modal === 'delete' && editingUser && (
        <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4">
          <div className="bg-white rounded-lg shadow-xl max-w-md w-full p-6">
            <h2 className="text-xl font-bold mb-4">Deaktiver bruker</h2>
            <p className="text-slate-600 mb-6">
              Er du sikker på at du vil deaktivere <strong>{editingUser.name || editingUser.email}</strong>?
              Brukeren vil ikke lenger kunne logge inn.
            </p>
            <div className="flex justify-end gap-2">
              <Button variant="outline" onClick={closeModal} disabled={submitting}>
                Avbryt
              </Button>
              <Button variant="destructive" onClick={handleDelete} disabled={submitting}>
                {submitting ? 'Deaktiverer...' : 'Deaktiver'}
              </Button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
