import axios from 'axios';
import { DayAheadResponse, SystemHealth } from '../types';

const api = axios.create({
  baseURL: import.meta.env.VITE_API_URL || '',
  timeout: 30000,
});

export const getHealth = async (): Promise<SystemHealth> => {
  const response = await api.get<SystemHealth>('/api/v1/health');
  return response.data;
};

export const getDayAheadData = async (
  date: string,
  cutoff: string = '12:00',
  forceRefresh: boolean = false
): Promise<DayAheadResponse> => {
  const response = await api.get<DayAheadResponse>('/api/v1/day-ahead', {
    params: {
      delivery_date: date,
      cutoff_time: cutoff,
      force_refresh: forceRefresh,
    },
  });
  return response.data;
};

export default api;
