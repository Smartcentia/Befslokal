"use client";
interface Props { onSearch?: (q: string) => void; getSuggestions?: (q: string) => Promise<any[]>; placeholder?: string; [k: string]: unknown; }
export default function SearchBar({ onSearch, placeholder }: Props) {
    return <input type="search" placeholder={placeholder || "Søk..."} onChange={e => onSearch?.(e.target.value)} className="border border-border rounded-lg px-3 py-2 text-sm w-full" />;
}
