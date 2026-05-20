import { fetchAPI } from './client';

export interface PredictBudgetRequest {
  year?: number;
  alpha?: number;
  beta?: number;
  inflation?: number;
  history_from?: number;
}

export interface PredictionResult {
  processed: number;
  skipped: number;
  errors: string[];
  year: number;
}

export async function triggerBudgetPrediction(
  params: PredictBudgetRequest = {}
): Promise<PredictionResult> {
  return fetchAPI('/financials/predict-budget', {
    method: 'POST',
    body: JSON.stringify({
      year: params.year ?? 2027,
      alpha: params.alpha ?? 0.7,
      beta: params.beta ?? 0.3,
      inflation: params.inflation ?? 0.035,
      history_from: params.history_from ?? 2021,
    }),
  });
}
