// Core client
export * from './client';
export { API_BASE_URL, BACKEND_URL, fetchAPI } from './client';

// Types
export * from '../types';

// ============================================================================
// API Modules - Organized by Domain
// ============================================================================

// --- Core Entities ---
export * from './propertiesApi';
export * from './unitsApi';
export * from './contractsApi';
export * from './partiesApi';

// --- Financial ---
export * from './costsApi';
export {
    getBudgetSummary as getBudgetSummaryApi,
    getPropertyBudget as getPropertyBudgetApi,
    type BudgetSummary as BudgetSummaryApi,
    type PropertyBudget as PropertyBudgetApi,
} from './budgetApi';
export * from './forecastApi';
export * from './financialAnalysisApi';
export * from './procurementApi';
export * from './accounting';

// --- HMS (Health, Safety & Environment) ---
export * from './riskApi';
export * from './hmsActivitiesApi';

// --- AI & Search ---
export * from './aiApi';
export * from './agentApi';
export * from './labApi';
export * from './searchApi';

// --- Dashboard & Analytics ---
export * from './dashboardApi';
export * from './transparencyApi';
export * from './overviewApi';

// --- Administration ---
export * from './adminApi';
export * from './userManagementApi';
export {
    getEconomicStatus as getEconomicImportStatus,
    previewFinancialCsv,
    importFinancialCsv,
    importMasterCsv,
    clearEconomicData,
    type EconomicStatus as EconomicImportStatus,
    type CsvPreviewResult,
    type ImportResult as EconomicImportResult,
    type MasterImportResult,
} from './economicImportApi';
export * from './scriptApprovalsApi';

// --- External Services ---
export * from './externalApi';
export * from './ssbApi';
export * from './barnevernApi';
export * from './jiraApi';

// --- Monitoring ---
export * from './mediaMonitorApi';
export * from './konkursMonitorApi';

// --- Location Services ---
export * from './bupLocationsApi';
export * from './centersApi';

// --- Files & Documents ---
export * from './filesApi';
export * from './indexingApi';
export { importApi, importEdon2, type Edon2ImportResult } from './importApi';

// --- Authentication ---
export * from './sessionsApi';
export * from './mfaApi';

// --- Reference Data ---
export * from './glossaryApi';
export * from './governanceApi';
export * from './ns3451Api';
export * from './componentsApi';

// --- MCP Services ---
export * from './mcpApi';

// ============================================================================
// Named Service Exports (for backward compatibility)
// ============================================================================

// Re-export aggregated service objects
export { unitsApi } from './unitsApi';
export { contractsApi } from './contractsApi';
export { partiesApi } from './partiesApi';
export { costsApi } from './costsApi';
export { forecastApi } from './forecastApi';
export { hmsActivitiesApi } from './hmsActivitiesApi';
export { externalApi } from './externalApi';
export { adminApi } from './adminApi';
export { dashboardApi } from './dashboardApi';
export { searchApi } from './searchApi';
export { centersApi } from './centersApi';
export { overviewApi } from './overviewApi';
export { mediaMonitorApi } from './mediaMonitorApi';
export { konkursMonitorApi } from './konkursMonitorApi';
export { filesApi } from './filesApi';
export { sessionsApi } from './sessionsApi';
export { mfaApi } from './mfaApi';
export { aiApi } from './aiApi';
export { agentApi } from './agentApi';
export { bupLocationsApi } from './bupLocationsApi';
export { indexingApi } from './indexingApi';
export { scriptApprovalsApi } from './scriptApprovalsApi';
export { mcpApi } from './mcpApi';

// ============================================================================
// Domain Services (re-exported for backward compatibility)
// ============================================================================

import { propertyService } from '../domains/core/propertyService';
import { riskService } from '../domains/hms/riskService';
import { agentService } from '../domains/innsikt/agentService';
import { searchService } from '../domains/innsikt/searchService';
import { deviationService } from '../domains/fdv/deviationService';
import { internalControlService } from '../domains/hms/internalControlService';
export type { InternalControlCase } from '../domains/hms/internalControlService';

// Individual function exports (legacy compatibility)
export const getProperty = propertyService.getById;
export const getRiskStats = riskService.getStats;
export const createRiskAssessment = riskService.create;
export const analyzeRisk = riskService.analyzeProperty;
export const chatWithAgent = agentService.chat;
export const getRegionalFinancials = (_year?: number) => agentService.getRegionalFinancials();
export const vectorSearch = searchService.vectorSearch;
export const globalSearch = searchService.globalSearch;
export const getDeviations = deviationService.getAll;
export const getInternalControlCases = internalControlService.getPropertyCases;

// Core Services (legacy exports)
export {
    getParty,
    fetchPartyCompanySummaryFromWeb,
    runPartyDueDiligence,
    enrichPartyBrreg,
    type DueDiligenceReport as LegacyDueDiligenceReport,
    runMediaMonitorSingle,
    type MediaMonitoringResult as LegacyMediaMonitoringResult,
} from '../services/coreService';

// Import Services (legacy exports)
export {
    analyzeImport,
    executeImport,
    type ImportAnalysisResponse,
    analyzeImport as legacyAnalyzeImport,
    executeImport as legacyExecuteImport,
} from '../services/importService';
