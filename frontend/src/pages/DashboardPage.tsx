import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { api } from '../api/client';

function StatCard({ label, value, sub }: { label: string; value: string | number; sub?: string }) {
  return (
    <div className="stat-card">
      <div className="stat-label">{label}</div>
      <div className="stat-value">{value}</div>
      {sub && <div className="stat-sub">{sub}</div>}
    </div>
  );
}

function sourceBadgeClass(name: string) {
  if (name === 'grailed') return 'badge badge-grailed';
  if (name === 'fashionphile') return 'badge badge-fashionphile';
  if (name === '1stdibs') return 'badge badge-1stdibs';
  return 'badge badge-other';
}

export default function DashboardPage() {
  const qc = useQueryClient();
  const { data, isLoading, isError } = useQuery({ queryKey: ['analytics'], queryFn: api.getAnalytics });
  const { mutate: refresh, isPending, isSuccess } = useMutation({
    mutationFn: api.triggerRefresh,
    onSuccess: () => qc.invalidateQueries({ queryKey: ['analytics'] }),
  });

  const totalAvgPrice = data?.by_source
    ? (data.by_source.reduce((s, r) => s + r.avg_price * r.total_products, 0)
        / Math.max(data.total_products, 1)).toFixed(2)
    : '--';

  return (
    <div>
      <div className="page-header">
        <h1 className="section-title" style={{ marginBottom: 0 }}>📊 Dashboard</h1>
        <div style={{ display: 'flex', alignItems: 'center', gap: '1rem' }}>
          {isPending && <span className="refresh-status">Refreshing…</span>}
          {isSuccess && !isPending && <span className="refresh-status ok">✓ Refreshed</span>}
          <button className="btn btn-primary" onClick={() => refresh()} disabled={isPending}>
            {isPending ? 'Refreshing…' : '↻ Refresh Data'}
          </button>
        </div>
      </div>

      {data?.last_refreshed_at && (
        <p style={{ fontSize: '0.8rem', color: 'var(--text-muted)', marginBottom: '1.5rem' }}>
          Last refreshed: {new Date(data.last_refreshed_at).toLocaleString()}
        </p>
      )}

      {isLoading && <div className="loading-state"><div className="spinner" />Loading analytics…</div>}
      {isError && <div className="error-state">Failed to load analytics. Is the backend running?</div>}

      {data && (
        <>
          <div className="stat-grid">
            <StatCard label="Total Products" value={data.total_products.toLocaleString()} />
            <StatCard label="Data Sources" value={data.by_source.length} />
            <StatCard label="Categories" value={data.by_category.length} />
            <StatCard label="Avg Price (USD)" value={`$${totalAvgPrice}`} />
          </div>

          <h2 className="section-title">By Marketplace</h2>
          <div className="source-grid">
            {data.by_source.map((s) => (
              <div key={s.source} className="source-card">
                <div className="source-name">
                  <span className={sourceBadgeClass(s.source)}>{s.source}</span>
                </div>
                <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '0.5rem', marginTop: '0.75rem' }}>
                  <div>
                    <div className="stat-label">Products</div>
                    <div style={{ fontWeight: 700 }}>{s.total_products}</div>
                  </div>
                  <div>
                    <div className="stat-label">Avg Price</div>
                    <div style={{ fontWeight: 700, color: 'var(--green)' }}>${s.avg_price.toFixed(0)}</div>
                  </div>
                  <div>
                    <div className="stat-label">Min</div>
                    <div style={{ fontSize: '0.875rem' }}>${s.min_price.toFixed(0)}</div>
                  </div>
                  <div>
                    <div className="stat-label">Max</div>
                    <div style={{ fontSize: '0.875rem' }}>${s.max_price.toFixed(0)}</div>
                  </div>
                </div>
              </div>
            ))}
          </div>

          <h2 className="section-title">By Category</h2>
          <div className="card table-wrap">
            <table>
              <thead>
                <tr>
                  <th>Category</th>
                  <th>Products</th>
                  <th>Avg Price (USD)</th>
                </tr>
              </thead>
              <tbody>
                {data.by_category.map((c) => (
                  <tr key={c.category}>
                    <td>{c.category}</td>
                    <td>{c.total_products}</td>
                    <td className="price-cell">${c.avg_price.toFixed(2)}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </>
      )}
    </div>
  );
}
