export function cn(...inputs: (string | undefined | null | false)[]) {
    return inputs.filter(Boolean).join(" ");
}
export async function safeFetch<T>(
    url: string,
    options?: RequestInit,
    fallbackValue?: T
): Promise<T | undefined> {
    try {
        const response = await fetch(url, options);
        if (!response.ok) {
            const errorText = await response.text().catch(() => "N/A");
            console.error(`[safeFetch] Error ${response.status} for ${url}:`, errorText);
            return fallbackValue;
        }
        return await response.json();
    } catch (error) {
        console.error(`[safeFetch] Fetch failed for ${url}:`, error);
        return fallbackValue;
    }
}
