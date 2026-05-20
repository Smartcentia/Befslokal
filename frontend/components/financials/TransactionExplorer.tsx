'use client';

import React, { useState, useEffect } from 'react';
import { getTransactions } from '../../lib/api/accounting';
import { GLTransaction } from '../../lib/types';
import { Search, ChevronLeft, ChevronRight, Filter, Download } from 'lucide-react';

export default function TransactionExplorer() {
    const [transactions, setTransactions] = useState<GLTransaction[]>([]);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState<string | null>(null);
    const [total, setTotal] = useState(0);
    const [totalPages, setTotalPages] = useState(0);

    const [page, setPage] = useState(1);
    const [pageSize, setPageSize] = useState(50);
    const [search, setSearch] = useState('');
    const [year, setYear] = useState<number | undefined>(undefined);
    const [month, setMonth] = useState<number | undefined>(undefined);

    const fetchData = async () => {
        setLoading(true);
        setError(null);
        try {
            const data = await getTransactions(page, pageSize, {
                year,
                month,
                search
            });
            setTransactions(data.items);
            setTotal(data.total);
            setTotalPages(data.total_pages);
        } catch (err: any) {
            setError(err.message || 'Failed to fetch data');
        } finally {
            setLoading(false);
        }
    };

    useEffect(() => {
        fetchData();
    }, [page, pageSize, year, month]);

    const handleSearch = (e: React.FormEvent) => {
        e.preventDefault();
        setPage(1); // Reset to first page on new search
        fetchData();
    };

    const formatCurrency = (amount: number) => {
        return new Intl.NumberFormat('no-NO', { style: 'currency', currency: 'NOK' }).format(amount);
    };

    const formatDate = (dateStr?: string) => {
        if (!dateStr) return '-';
        return new Date(dateStr).toLocaleDateString('no-NO');
    };

    return (
        <div className="bg-white rounded-xl shadow-sm border border-gray-200 overflow-hidden">
            <div className="p-6 border-b border-gray-200 bg-gray-50 flex flex-col md:flex-row justify-between items-start md:items-center gap-4">
                <div>
                    <h2 className="text-xl font-semibold text-gray-900">Transaksjoner</h2>
                    <p className="text-sm text-gray-500">Detaljert regnskapsoversikt ({total} poster)</p>
                </div>

                <form onSubmit={handleSearch} className="flex gap-2 w-full md:w-auto">
                    <div className="relative flex-1 md:w-64">
                        <Search className="absolute left-3 top-2.5 h-4 w-4 text-gray-400" />
                        <input
                            type="text"
                            placeholder="Søk (leverandør, bilag...)"
                            className="w-full pl-9 pr-4 py-2 border border-gray-300 rounded-lg text-sm focus:ring-1 focus:ring-indigo-500"
                            value={search}
                            onChange={(e) => setSearch(e.target.value)}
                        />
                    </div>
                    <button type="submit" className="px-4 py-2 bg-indigo-600 text-white rounded-lg text-sm font-medium hover:bg-indigo-700">
                        Søk
                    </button>
                </form>
            </div>

            {/* Filters */}
            <div className="flex gap-4 p-4 border-b border-gray-200 bg-white">
                <select
                    className="border border-gray-300 rounded-lg text-sm p-2 w-32"
                    value={year || ''}
                    onChange={(e) => {
                        const val = e.target.value ? parseInt(e.target.value) : undefined;
                        setYear(val);
                        setPage(1);
                    }}
                >
                    <option value="">Alle år</option>
                    {[2024, 2025, 2026].map(y => <option key={y} value={y}>{y}</option>)}
                </select>

                <select
                    className="border border-gray-300 rounded-lg text-sm p-2 w-32"
                    value={month || ''}
                    onChange={(e) => {
                        const val = e.target.value ? parseInt(e.target.value) : undefined;
                        setMonth(val);
                        setPage(1);
                    }}
                >
                    <option value="">Alle mnd</option>
                    {Array.from({ length: 12 }, (_, i) => i + 1).map(m => (
                        <option key={m} value={m}>{new Date(2000, m - 1, 1).toLocaleString('no-NO', { month: 'long' })}</option>
                    ))}
                </select>

                <div className="ml-auto">
                    <button className="flex items-center gap-2 text-sm text-gray-600 hover:text-gray-900">
                        <Download className="w-4 h-4" />
                        Eksporter
                    </button>
                </div>
            </div>

            {/* Table */}
            <div className="overflow-x-auto">
                <table className="min-w-full divide-y divide-gray-200">
                    <thead className="bg-gray-50">
                        <tr>
                            <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Dato</th>
                            <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Leverandør / Tekst</th>
                            <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Konto</th>
                            <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Avdeling</th>
                            <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Region</th>
                            <th className="px-6 py-3 text-right text-xs font-medium text-gray-500 uppercase tracking-wider">Beløp</th>
                        </tr>
                    </thead>
                    <tbody className="bg-white divide-y divide-gray-200">
                        {loading ? (
                            <tr>
                                <td colSpan={6} className="px-6 py-12 text-center text-gray-500">
                                    Laster transaksjoner...
                                </td>
                            </tr>
                        ) : transactions.length === 0 ? (
                            <tr>
                                <td colSpan={6} className="px-6 py-12 text-center text-gray-500">
                                    Ingen transaksjoner funnet.
                                </td>
                            </tr>
                        ) : (
                            transactions.map((tx) => (
                                <tr key={tx.transaction_id} className="hover:bg-gray-50">
                                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                                        {formatDate(tx.transaction_date || undefined)}
                                        <div className="text-xs text-gray-400">{tx.year}-{tx.month}</div>
                                    </td>
                                    <td className="px-6 py-4 text-sm text-gray-900">
                                        <div className="font-medium">{tx.supplier_name || 'Ukjent'}</div>
                                        <div className="text-gray-500 truncate max-w-xs">{tx.description}</div>
                                        {tx.invoice_number && <div className="text-xs text-indigo-500">Faktura: {tx.invoice_number}</div>}
                                    </td>
                                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                                        <div className="font-mono">{tx.account_code}</div>
                                        <div className="text-xs">{tx.account_name}</div>
                                    </td>
                                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                                        <div>{tx.department_name}</div>
                                        <div className="text-xs text-gray-400">{tx.department_code}</div>
                                    </td>
                                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                                        {tx.region_name}
                                    </td>
                                    <td className={`px-6 py-4 whitespace-nowrap text-sm text-right font-medium ${tx.amount < 0 ? 'text-red-600' : 'text-gray-900'}`}>
                                        {formatCurrency(tx.amount)}
                                    </td>
                                </tr>
                            ))
                        )}
                    </tbody>
                </table>
            </div>

            {/* Pagination */}
            <div className="bg-white px-4 py-3 flex items-center justify-between border-t border-gray-200 sm:px-6">
                <div className="flex-1 flex justify-between sm:hidden">
                    <button
                        onClick={() => setPage(p => Math.max(1, p - 1))}
                        disabled={page === 1}
                        className="relative inline-flex items-center px-4 py-2 border border-gray-300 text-sm font-medium rounded-md text-gray-700 bg-white hover:bg-gray-50 disabled:opacity-50"
                    >
                        Forrige
                    </button>
                    <button
                        onClick={() => setPage(p => Math.min(totalPages, p + 1))}
                        disabled={page === totalPages}
                        className="ml-3 relative inline-flex items-center px-4 py-2 border border-gray-300 text-sm font-medium rounded-md text-gray-700 bg-white hover:bg-gray-50 disabled:opacity-50"
                    >
                        Neste
                    </button>
                </div>
                <div className="hidden sm:flex-1 sm:flex sm:items-center sm:justify-between">
                    <div>
                        <p className="text-sm text-gray-700">
                            Viser <span className="font-medium">{(page - 1) * pageSize + 1}</span> til <span className="font-medium">{Math.min(page * pageSize, total)}</span> av <span className="font-medium">{total}</span> resultater
                        </p>
                    </div>
                    <div>
                        <nav className="relative z-0 inline-flex rounded-md shadow-sm -space-x-px" aria-label="Pagination">
                            <button
                                onClick={() => setPage(p => Math.max(1, p - 1))}
                                disabled={page === 1}
                                className="relative inline-flex items-center px-2 py-2 rounded-l-md border border-gray-300 bg-white text-sm font-medium text-gray-500 hover:bg-gray-50 disabled:opacity-50"
                            >
                                <span className="sr-only">Forrige</span>
                                <ChevronLeft className="h-5 w-5" aria-hidden="true" />
                            </button>
                            <span className="relative inline-flex items-center px-4 py-2 border border-gray-300 bg-white text-sm font-medium text-gray-700">
                                Side {page} av {totalPages}
                            </span>
                            <button
                                onClick={() => setPage(p => Math.min(totalPages, p + 1))}
                                disabled={page === totalPages}
                                className="relative inline-flex items-center px-2 py-2 rounded-r-md border border-gray-300 bg-white text-sm font-medium text-gray-500 hover:bg-gray-50 disabled:opacity-50"
                            >
                                <span className="sr-only">Neste</span>
                                <ChevronRight className="h-5 w-5" aria-hidden="true" />
                            </button>
                        </nav>
                    </div>
                </div>
            </div>
        </div>
    );
}
