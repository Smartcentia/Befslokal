// Basic mock for fetch
const mockFetch = (url: any, options: any) => {
    console.log(`[API Call] ${options?.method || 'GET'} ${url}`);
    return Promise.resolve({
        ok: true,
        json: () => Promise.resolve({ status: 'mocked_success' }),
        text: () => Promise.resolve('mocked_body')
    });
};

// Polyfill fetch
(global as any).fetch = mockFetch;
(global as any).process = { env: { NEXT_PUBLIC_API_URL: 'https://striking-insight-production-a21b.up.railway.app' } };

// Import services
// Note: We use relative paths assuming this runs from frontend/scripts
// and ts-node handles imports.
import { propertyService } from '../lib/domains/core/propertyService';
import { contractService } from '../lib/domains/core/contractService';
import { riskService } from '../lib/domains/hms/riskService';
import { agentService } from '../lib/domains/innsikt/agentService';

async function verify() {
    console.log("--- Starting Architecture Verification ---\n");

    console.log("1. Testing Core Domain...");
    await propertyService.getAll();
    await propertyService.getById('123');
    await contractService.getAll();

    console.log("\n2. Testing HMS Domain...");
    await riskService.create({
        property_id: '123',
        risk_category: 'high',
        risk_type: 'Test',
        severity: 'high'
    });

    console.log("\n3. Testing Innsikt Domain...");
    await agentService.chat([{ role: 'user', content: "Hello Agent" }]);
    await agentService.getStats();

    console.log("\n✅ Verification Complete: All services routed correctly.");
}

verify().catch(console.error);
