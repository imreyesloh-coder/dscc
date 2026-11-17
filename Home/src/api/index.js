import * as mock from './mockApi.js';
import * as real from './realApi.js';

const useMock = import.meta.env.VITE_USE_MOCK === 'true';
const api = useMock ? mock : real;

export const { getHomeData, updateStations, getTrainingPlan, setDayDone, requestPlanChange, getStats } = api;

if (!useMock) real.wakeBackend();
