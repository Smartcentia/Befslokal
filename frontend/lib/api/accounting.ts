import { TransactionListResponse } from '../types';
import { fetchAPI } from './client';

export async function getTransactions(
    page: number = 1,
    size: number = 50,
    filters: {
        property_id?: string;
        year?: number;
        month?: number;
        search?: string;
        account_code?: string;
    } = {}
): Promise<TransactionListResponse> {
    const params = new URLSearchParams();
    params.append('page', page.toString());
    params.append('size', size.toString());

    if (filters.property_id) params.append('property_id', filters.property_id);
    if (filters.year) params.append('year', filters.year.toString());
    if (filters.month) params.append('month', filters.month.toString());
    if (filters.search) params.append('search', filters.search);
    if (filters.account_code) params.append('account_code', filters.account_code);

    return fetchAPI(`/accounting/transactions?${params.toString()}`, { method: 'GET' });
}
