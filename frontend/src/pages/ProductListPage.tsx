import { useState } from 'react';
import { useQuery } from '@tanstack/react-query';
import { useNavigate } from 'react-router-dom';
import { api } from '../api/client';
import type { ProductFilters } from '../api/client';

const SOURCES = ['grailed', 'fashionphile', '1stdibs'];

export default function ProductListPage() {
  const navigate = useNavigate();
  const [filters, setFilters] = useState<ProductFilters>({ page: 1, size: 20 });
  const [draft, setDraft] = useState<ProductFilters>({});

  const { data, isLoading, isError } = useQuery({
    queryKey: ['products', filters],
    queryFn: () => api.getProducts(filters),
  });

  const applyFilters = () => setFilters({ ...draft, page: 1, size: 20 });
  const clearFilters = () => { setDraft({}); setFilters({ page: 1, size: 20 }); };

  const totalPages = data ? Math.ceil(data.total / (filters.size || 20)) : 1;

  return (
    <div>
      <div className="page-header">
        <h1 className="section-title" style={{ marginBottom: 0 }}>🛍️ Products</h1>
        {data && <span className="refresh-status">{data.total.toLocaleString()} results</span>}
      </div>

      {/* Filter Bar */}
      <div className="card" style={{ marginBottom: '1.5rem' }}>
        <div className="filter-bar">
          <div className="filter-group">
            <label className="filter-label">Source</label>
            <select value={draft.source || ''} onChange={(e) => setDraft({ ...draft, source: e.target.value || undefined })}>
              <option value="">All Sources</option>
              {SOURCES.map((s) => <option key={s} value={s}>{s}</option>)}
            </select>
          </div>
          <div className="filter-group">
            <label className="filter-label">Brand</label>
            <input
              type="text"
              placeholder="e.g. Chanel"
              value={draft.brand || ''}
              onChange={(e) => setDraft({ ...draft, brand: e.target.value || undefined })}
            />
          </div>
          <div className="filter-group">
            <label className="filter-label">Min Price $</label>
            <input
              type="number"
              placeholder="0"
              min={0}
              value={draft.min_price ?? ''}
              onChange={(e) => setDraft({ ...draft, min_price: e.target.value ? Number(e.target.value) : undefined })}
            />
          </div>
          <div className="filter-group">
            <label className="filter-label">Max Price $</label>
            <input
              type="number"
              placeholder="∞"
              min={0}
              value={draft.max_price ?? ''}
              onChange={(e) => setDraft({ ...draft, max_price: e.target.value ? Number(e.target.value) : undefined })}
            />
          </div>
          <button className="btn btn-primary" onClick={applyFilters}>Apply</button>
          <button className="btn btn-ghost" onClick={clearFilters}>Clear</button>
        </div>
      </div>

      {isLoading && <div className="loading-state"><div className="spinner" />Loading products…</div>}
      {isError && <div className="error-state">Failed to load products.</div>}

      {data && (
        <>
          <div className="card table-wrap">
            <table>
              <thead>
                <tr>
                  <th>Product</th>
                  <th>Brand</th>
                  <th>Source</th>
                  <th>Category</th>
                  <th>Condition</th>
                  <th>Price (USD)</th>
                  <th>Last Seen</th>
                </tr>
              </thead>
              <tbody>
                {data.items.length === 0 && (
                  <tr><td colSpan={7} className="empty-state">No products found.</td></tr>
                )}
                {data.items.map((p) => (
                  <tr key={p.id} onClick={() => navigate(`/products/${p.id}`)}>
                    <td style={{ maxWidth: 260, overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>{p.title}</td>
                    <td>{p.brand}</td>
                    <td>
                      <span className={`badge badge-${p.source_name}`}>{p.source_name}</span>
                    </td>
                    <td>{p.category_name || '—'}</td>
                    <td style={{ color: 'var(--text-muted)' }}>{p.condition || '—'}</td>
                    <td className="price-cell">${Number(p.current_price).toFixed(2)}</td>
                    <td style={{ color: 'var(--text-muted)', fontSize: '0.8rem' }}>
                      {new Date(p.last_seen_at).toLocaleDateString()}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>

          {/* Pagination */}
          <div className="pagination">
            <button
              className="btn btn-ghost"
              disabled={(filters.page || 1) <= 1}
              onClick={() => setFilters({ ...filters, page: (filters.page || 1) - 1 })}
            >← Prev</button>
            <span className="page-info">Page {filters.page} of {totalPages}</span>
            <button
              className="btn btn-ghost"
              disabled={(filters.page || 1) >= totalPages}
              onClick={() => setFilters({ ...filters, page: (filters.page || 1) + 1 })}
            >Next →</button>
          </div>
        </>
      )}
    </div>
  );
}
