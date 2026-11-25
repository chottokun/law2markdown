import {
  BarController,
  BarElement,
  CategoryScale,
  Chart,
  Legend,
  LinearScale,
  Tooltip,
} from 'chart.js';
import { Download, Play, Terminal } from 'lucide-react';
import { useEffect, useRef, useState } from 'react';
import { SQL_PRESETS } from '../lib/constants';
import { fetchAnalyticsSummary, runSandboxSql } from '../lib/queries';
import { rowsToCsv } from '../lib/sqlSafety';
import type { AnalyticsSummary, SqlQueryResult } from '../lib/types';

Chart.register(BarController, CategoryScale, LinearScale, BarElement, Tooltip, Legend);

interface AnalyticsTabProps {
  onOpenLawInViewer: (lawId: string) => void;
  onNotify: (kind: 'info' | 'success' | 'error', text: string) => void;
}

function triggerDownload(filename: string, mimeType: string, content: string) {
  const blob = new Blob([content], { type: mimeType });
  const url = URL.createObjectURL(blob);
  const link = document.createElement('a');
  link.href = url;
  link.download = filename;
  document.body.appendChild(link);
  link.click();
  document.body.removeChild(link);
  URL.revokeObjectURL(url);
}

export function AnalyticsTab({ onOpenLawInViewer, onNotify }: AnalyticsTabProps) {
  const [summary, setSummary] = useState<AnalyticsSummary | null>(null);
  const [loadingSummary, setLoadingSummary] = useState(true);

  const [sqlText, setSqlText] = useState(SQL_PRESETS[0].sql);
  const [sqlResult, setSqlResult] = useState<SqlQueryResult | null>(null);
  const [sqlError, setSqlError] = useState<string | null>(null);
  const [runningSql, setRunningSql] = useState(false);

  const eraCanvasRef = useRef<HTMLCanvasElement | null>(null);
  const topArticlesCanvasRef = useRef<HTMLCanvasElement | null>(null);
  const topTermsCanvasRef = useRef<HTMLCanvasElement | null>(null);

  useEffect(() => {
    let cancelled = false;
    setLoadingSummary(true);
    fetchAnalyticsSummary()
      .then((res) => {
        if (!cancelled) setSummary(res);
      })
      .catch((err) => {
        if (!cancelled) {
          onNotify('error', err instanceof Error ? err.message : '統計データの集計に失敗しました');
        }
      })
      .finally(() => {
        if (!cancelled) setLoadingSummary(false);
      });
    return () => {
      cancelled = true;
    };
  }, []);

  // Chart.js インスタンス描画
  useEffect(() => {
    if (!summary) return;
    const charts: Chart[] = [];

    if (eraCanvasRef.current) {
      charts.push(
        new Chart(eraCanvasRef.current, {
          type: 'bar',
          data: {
            labels: summary.eraDistribution.map((d) => d.era),
            datasets: [
              {
                label: '法令数',
                data: summary.eraDistribution.map((d) => d.count),
                backgroundColor: ['#64748b', '#94a3b8', '#38bdf8', '#818cf8', '#10b981', '#475569'],
                borderRadius: 6,
              },
            ],
          },
          options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: { legend: { display: false } },
            scales: {
              x: { ticks: { color: '#cbd5e1' }, grid: { display: false } },
              y: { ticks: { color: '#94a3b8' }, grid: { color: 'rgba(148,163,184,0.12)' } },
            },
          },
        }),
      );
    }

    if (topArticlesCanvasRef.current) {
      charts.push(
        new Chart(topArticlesCanvasRef.current, {
          type: 'bar',
          data: {
            labels: summary.topLawsByArticles.map((d) =>
              d.law_title.length > 14 ? `${d.law_title.slice(0, 14)}…` : d.law_title,
            ),
            datasets: [
              {
                label: '条文数',
                data: summary.topLawsByArticles.map((d) => d.count),
                backgroundColor: '#38bdf8',
                borderRadius: 4,
              },
            ],
          },
          options: {
            indexAxis: 'y',
            responsive: true,
            maintainAspectRatio: false,
            onClick: (_evt, elements) => {
              if (elements.length > 0) {
                const idx = elements[0].index;
                const target = summary.topLawsByArticles[idx];
                if (target) onOpenLawInViewer(target.law_id);
              }
            },
            plugins: { legend: { display: false } },
            scales: {
              x: { ticks: { color: '#94a3b8' }, grid: { color: 'rgba(148,163,184,0.12)' } },
              y: { ticks: { color: '#cbd5e1', font: { size: 11 } }, grid: { display: false } },
            },
          },
        }),
      );
    }

    if (topTermsCanvasRef.current) {
      charts.push(
        new Chart(topTermsCanvasRef.current, {
          type: 'bar',
          data: {
            labels: summary.topLawsByTerms.map((d) =>
              d.law_title.length > 14 ? `${d.law_title.slice(0, 14)}…` : d.law_title,
            ),
            datasets: [
              {
                label: '定義用語数',
                data: summary.topLawsByTerms.map((d) => d.count),
                backgroundColor: '#10b981',
                borderRadius: 4,
              },
            ],
          },
          options: {
            indexAxis: 'y',
            responsive: true,
            maintainAspectRatio: false,
            onClick: (_evt, elements) => {
              if (elements.length > 0) {
                const idx = elements[0].index;
                const target = summary.topLawsByTerms[idx];
                if (target) onOpenLawInViewer(target.law_id);
              }
            },
            plugins: { legend: { display: false } },
            scales: {
              x: { ticks: { color: '#94a3b8' }, grid: { color: 'rgba(148,163,184,0.12)' } },
              y: { ticks: { color: '#cbd5e1', font: { size: 11 } }, grid: { display: false } },
            },
          },
        }),
      );
    }

    return () => {
      for (const chart of charts) {
        chart.destroy();
      }
    };
  }, [summary]);

  const handleRunSql = async () => {
    setSqlError(null);
    setRunningSql(true);
    try {
      const result = await runSandboxSql(sqlText);
      setSqlResult(result);
    } catch (err) {
      setSqlError(err instanceof Error ? err.message : 'クエリの実行に失敗しました');
    } finally {
      setRunningSql(false);
    }
  };

  return (
    <div className="analytics-scroll">
      <div className="analytics-container">
        {loadingSummary || !summary ? (
          <div className="panel-card">
            <div className="empty-state">全法令データセットを集計中です...</div>
          </div>
        ) : (
          <>
            <div className="kpi-grid">
              <div className="kpi-card">
                <div className="kpi-label">収録法令数</div>
                <div className="kpi-value">{summary.totalLaws.toLocaleString()}</div>
              </div>
              <div className="kpi-card">
                <div className="kpi-label">総条文レコード数</div>
                <div className="kpi-value">{summary.totalArticles.toLocaleString()}</div>
              </div>
              <div className="kpi-card">
                <div className="kpi-label">抽出された条文参照数</div>
                <div className="kpi-value">{summary.totalOutboundEdges.toLocaleString()}</div>
              </div>
              <div className="kpi-card">
                <div className="kpi-label">抽出された定義用語数</div>
                <div className="kpi-value">{summary.totalDefinedTerms.toLocaleString()}</div>
              </div>
            </div>

            <div className="charts-grid">
              <div className="panel-card">
                <h3>元号別の法令分布</h3>
                <div className="chart-wrap">
                  <canvas ref={eraCanvasRef} />
                </div>
              </div>
              <div className="panel-card">
                <h3>
                  <span>条文数 Top 15 法令</span>
                  <span style={{ fontSize: '0.74rem', color: '#94a3b8' }}>棒クリックで開く</span>
                </h3>
                <div className="chart-wrap">
                  <canvas ref={topArticlesCanvasRef} />
                </div>
              </div>
              <div className="panel-card">
                <h3>
                  <span>定義用語数 Top 10 法令</span>
                  <span style={{ fontSize: '0.74rem', color: '#94a3b8' }}>棒クリックで開く</span>
                </h3>
                <div className="chart-wrap">
                  <canvas ref={topTermsCanvasRef} />
                </div>
              </div>
            </div>
          </>
        )}

        <section className="panel-card">
          <h3>
            <span style={{ display: 'inline-flex', alignItems: 'center', gap: '0.45rem' }}>
              <Terminal size={16} color="#38bdf8" />
              DuckDB-Wasm SQL Sandbox（テーブル名: <code>laws_articles</code>）
            </span>
          </h3>

          <div className="chip-row" style={{ marginBottom: '0.75rem' }}>
            {SQL_PRESETS.map((preset) => (
              <button
                key={preset.id}
                type="button"
                className="chip"
                title={preset.description}
                onClick={() => setSqlText(preset.sql)}
              >
                {preset.label}
              </button>
            ))}
          </div>

          <textarea
            className="sql-editor"
            value={sqlText}
            onChange={(e) => setSqlText(e.target.value)}
            onKeyDown={(e) => {
              if ((e.ctrlKey || e.metaKey) && e.key === 'Enter') {
                e.preventDefault();
                void handleRunSql();
              }
            }}
            spellCheck={false}
          />

          <div
            style={{
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'space-between',
              flexWrap: 'wrap',
              gap: '0.6rem',
              marginTop: '0.65rem',
            }}
          >
            <div style={{ display: 'flex', alignItems: 'center', gap: '0.6rem' }}>
              <button
                type="button"
                className="btn primary"
                disabled={runningSql}
                onClick={handleRunSql}
              >
                <Play size={14} />
                {runningSql ? '実行中...' : 'SQL を実行 (Ctrl+Enter)'}
              </button>
              {sqlResult && (
                <span style={{ fontSize: '0.8rem', color: '#94a3b8' }}>
                  {sqlResult.rows.length} 行取得 ({sqlResult.elapsedMs} ms)
                  {sqlResult.truncated ? ' ※最大500行まで表示' : ''}
                </span>
              )}
            </div>

            {sqlResult && sqlResult.rows.length > 0 && (
              <div style={{ display: 'flex', gap: '0.45rem' }}>
                <button
                  type="button"
                  className="btn"
                  onClick={() =>
                    triggerDownload(
                      'laws_query_result.csv',
                      'text/csv;charset=utf-8',
                      rowsToCsv(sqlResult.columns, sqlResult.rows),
                    )
                  }
                >
                  <Download size={14} />
                  CSV
                </button>
                <button
                  type="button"
                  className="btn"
                  onClick={() =>
                    triggerDownload(
                      'laws_query_result.json',
                      'application/json;charset=utf-8',
                      JSON.stringify(sqlResult.rows, null, 2),
                    )
                  }
                >
                  <Download size={14} />
                  JSON
                </button>
              </div>
            )}
          </div>

          {sqlError && (
            <div className="error-banner" style={{ marginTop: '0.75rem' }}>
              {sqlError}
            </div>
          )}

          {sqlResult && sqlResult.columns.length > 0 && (
            <div className="table-wrap">
              <table className="data-table">
                <thead>
                  <tr>
                    {sqlResult.columns.map((col) => (
                      <th key={col}>{col}</th>
                    ))}
                  </tr>
                </thead>
                <tbody>
                  {sqlResult.rows.map((row, idx) => (
                    <tr key={idx}>
                      {sqlResult.columns.map((col) => {
                        const val = row[col];
                        const display =
                          val === null || val === undefined
                            ? ''
                            : Array.isArray(val) || typeof val === 'object'
                              ? JSON.stringify(val)
                              : String(val);
                        return (
                          <td key={col} title={display}>
                            {display}
                          </td>
                        );
                      })}
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </section>
      </div>
    </div>
  );
}
