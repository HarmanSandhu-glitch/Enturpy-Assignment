import { useParams, useNavigate } from 'react-router-dom';
import { useQuery } from '@tanstack/react-query';
import {
  LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer,
} from 'recharts';
import { api } from '../api/client';

export default function ProductDetailPage() {
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();
  const { data, isLoading, isError } = useQuery({
    queryKey: ['product', id],
    queryFn: () => api.getProduct(Number(id)),
    enabled: !!id,
  });

  const chartData = data?.price_history
    .slice()
    .reverse()
    .map((h) => ({
      date: new Date(h.recorded_at).toLocaleDateString(),
      price: Number(h.price),
    })) ?? [];

  if (isLoading) return <div className="loading-state"><div className="spinner" />Loading product…</div>;
  if (isError || !data) return <div className="error-state">Product not found.</div>;

  return (
    <div>
      <button className="back-link btn btn-ghost" onClick={() => navigate(-1)}>
        ← Back to Products
      </button>

      <div className="detail-grid">
        {/* Image */}
        <div>
          {data.image_url
            ? <img src={data.image_url} alt={data.title} className="product-image" onError={(e) => { (e.target as HTMLImageElement).style.display = 'none'; }} />
            : <div className="product-image-placeholder">🛍️</div>
          }
        </div>

        {/* Info */}
        <div className="card">
          <div className="product-meta-row">
            <span className={`badge badge-${data.source_name}`}>{data.source_name}</span>
            {data.category_name && <span style={{ color: 'var(--text-muted)' }}>• {data.category_name}</span>}
          </div>

          <h1 className="product-title">{data.title}</h1>
          <div className="product-price">${Number(data.current_price).toFixed(2)} <span style={{ fontSize: '1rem', color: 'var(--text-muted)' }}>USD</span></div>

          <div className="info-grid">
            <div className="info-row">
              <span className="info-key">Brand</span>
              <span className="info-val">{data.brand || '—'}</span>
            </div>
            <div className="info-row">
              <span className="info-key">Condition</span>
              <span className="info-val">{data.condition || '—'}</span>
            </div>
            <div className="info-row">
              <span className="info-key">External ID</span>
              <span className="info-val" style={{ fontSize: '0.75rem', wordBreak: 'break-all' }}>{data.external_id}</span>
            </div>
            <div className="info-row">
              <span className="info-key">Last Seen</span>
              <span className="info-val">{new Date(data.last_seen_at).toLocaleString()}</span>
            </div>
          </div>

          <div style={{ marginTop: '1rem' }}>
            <a href={data.url} target="_blank" rel="noreferrer" className="btn btn-ghost" style={{ width: '100%', justifyContent: 'center', marginTop: '0.5rem' }}>
              View on {data.source_name} ↗
            </a>
          </div>
        </div>
      </div>

      {/* Price History Chart */}
      <div className="card chart-wrap" style={{ marginTop: '1.5rem' }}>
        <h2 className="section-title">📈 Price History ({data.price_history.length} records)</h2>
        {chartData.length < 2 ? (
          <div className="empty-state" style={{ padding: '2rem' }}>
            Only {chartData.length} data point(s) — run a refresh to build history.
          </div>
        ) : (
          <ResponsiveContainer width="100%" height={260}>
            <LineChart data={chartData} margin={{ top: 10, right: 20, left: 0, bottom: 0 }}>
              <CartesianGrid strokeDasharray="3 3" stroke="var(--border)" />
              <XAxis dataKey="date" tick={{ fill: 'var(--text-muted)', fontSize: 11 }} />
              <YAxis
                tick={{ fill: 'var(--text-muted)', fontSize: 11 }}
                tickFormatter={(v) => `$${v}`}
                width={70}
              />
              <Tooltip
                contentStyle={{ background: 'var(--bg-card2)', border: '1px solid var(--border)', borderRadius: 8 }}
                labelStyle={{ color: 'var(--text-muted)' }}
                itemStyle={{ color: 'var(--green)' }}
                formatter={(v) => [`$${Number(v).toFixed(2)}`, 'Price']}
              />
              <Line
                type="monotone"
                dataKey="price"
                stroke="var(--accent2)"
                strokeWidth={2}
                dot={{ fill: 'var(--accent)', r: 3 }}
                activeDot={{ r: 5 }}
              />
            </LineChart>
          </ResponsiveContainer>
        )}

        {/* Raw history table */}
        <div className="table-wrap" style={{ marginTop: '1rem' }}>
          <table>
            <thead>
              <tr>
                <th>#</th>
                <th>Price</th>
                <th>Currency</th>
                <th>Recorded At</th>
              </tr>
            </thead>
            <tbody>
              {data.price_history.map((h, i) => (
                <tr key={h.id}>
                  <td style={{ color: 'var(--text-muted)', fontSize: '0.8rem' }}>{i + 1}</td>
                  <td className="price-cell">${Number(h.price).toFixed(2)}</td>
                  <td style={{ color: 'var(--text-muted)' }}>{h.currency}</td>
                  <td style={{ color: 'var(--text-muted)', fontSize: '0.8rem' }}>
                    {new Date(h.recorded_at).toLocaleString()}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
}
