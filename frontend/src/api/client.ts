import axios from 'axios';

const API_KEY = import.meta.env.VITE_API_KEY || 'dev-key';
const BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';

const client = axios.create({
  baseURL: BASE_URL,
  headers: { 'X-API-Key': API_KEY },
});

export interface PriceHistory {
  id: number;
  price: string;
  currency: string;
  recorded_at: string;
}

export interface Product {
  id: number;
  external_id: string;
  title: string;
  brand: string;
  model: string;
  condition: string | null;
  url: string;
  image_url: string | null;
  current_price: string;
  currency: string;
  last_seen_at: string;
  source_name: string | null;
  category_name: string | null;
}

export interface ProductDetail extends Product {
  price_history: PriceHistory[];
}

export interface PaginatedProducts {
  total: number;
  page: number;
  size: number;
  items: Product[];
}

export interface SourceStat {
  source: string;
  total_products: number;
  avg_price: number;
  min_price: number;
  max_price: number;
}

export interface CategoryStat {
  category: string;
  total_products: number;
  avg_price: number;
}

export interface Analytics {
  total_products: number;
  by_source: SourceStat[];
  by_category: CategoryStat[];
  last_refreshed_at: string | null;
}

export interface ProductFilters {
  source?: string;
  category?: string;
  min_price?: number;
  max_price?: number;
  brand?: string;
  page?: number;
  size?: number;
}

export const api = {
  getAnalytics: () =>
    client.get<Analytics>('/api/analytics').then((r) => r.data),

  getProducts: (filters: ProductFilters = {}) => {
    const params = Object.fromEntries(
      Object.entries(filters).filter(([, v]) => v !== undefined && v !== '')
    );
    return client.get<PaginatedProducts>('/api/products', { params }).then((r) => r.data);
  },

  getProduct: (id: number) =>
    client.get<ProductDetail>(`/api/products/${id}`).then((r) => r.data),

  triggerRefresh: () =>
    client.post('/api/refresh/sync').then((r) => r.data),
};
