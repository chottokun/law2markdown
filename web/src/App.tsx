import { BarChart3, BookOpen, ExternalLink, Network, Scale } from 'lucide-react';
import { useCallback, useEffect, useState } from 'react';
import { AnalyticsTab } from './components/AnalyticsTab';
import { GraphTab } from './components/GraphTab';
import { ViewerTab } from './components/ViewerTab';
import { CORE_LAWS, GITHUB_REPO_URL, HF_DATASET_URL } from './lib/constants';
import { fetchLawCatalog } from './lib/queries';
import type { DbStatus, LawCatalogEntry, TabId, ToastMessage } from './lib/types';

function parseHashState(): { tab: TabId; lawId: string | null; articleNum: string | null } {
  const raw = window.location.hash.replace(/^#\/?/, '');
  const [pathPart, queryPart] = raw.split('?');
  const tab: TabId =
    pathPart === 'graph' || pathPart === 'analytics' || pathPart === 'viewer'
      ? pathPart
      : 'viewer';
  const params = new URLSearchParams(queryPart ?? '');
  return {
    tab,
    lawId: params.get('law'),
    articleNum: params.get('article'),
  };
}

function writeHashState(tab: TabId, lawId: string | null, articleNum: string | null) {
  const params = new URLSearchParams();
  if (lawId) params.set('law', lawId);
  if (articleNum && tab !== 'analytics') params.set('article', articleNum);
  const qs = params.toString();
  const nextHash = qs ? `#/${tab}?${qs}` : `#/${tab}`;
  if (window.location.hash !== nextHash) {
    window.history.replaceState(null, '', nextHash);
  }
}

export function App() {
  const initial = parseHashState();
  const [activeTab, setActiveTab] = useState<TabId>(initial.tab);
  const [selectedLawId, setSelectedLawId] = useState<string | null>(initial.lawId);
  const [selectedArticleNum, setSelectedArticleNum] = useState<string | null>(
    initial.articleNum,
  );

  const [dbStatus, setDbStatus] = useState<DbStatus>('initializing');
  const [dbError, setDbError] = useState<string | null>(null);
  const [catalog, setCatalog] = useState<LawCatalogEntry[]>([]);
  const [toasts, setToasts] = useState<ToastMessage[]>([]);

  const notify = useCallback((kind: 'info' | 'success' | 'error', text: string) => {
    const id = Date.now() + Math.floor(Math.random() * 1000);
    setToasts((prev) => [...prev, { id, kind, text }]);
    window.setTimeout(() => {
      setToasts((prev) => prev.filter((t) => t.id !== id));
    }, 3600);
  }, []);

  useEffect(() => {
    let cancelled = false;
    setDbStatus('initializing');
    fetchLawCatalog()
      .then((list) => {
        if (cancelled) return;
        setCatalog(list);
        setDbStatus('ready');

        if (!selectedLawId && list.length > 0) {
          const preferred =
            list.find((l) => l.law_id.startsWith(CORE_LAWS[0].idPrefix)) ??
            list.find((l) => l.law_id.startsWith(CORE_LAWS[1].idPrefix)) ??
            list[0];
          setSelectedLawId(preferred.law_id);
        }
      })
      .catch((err) => {
        if (cancelled) return;
        setDbStatus('error');
        setDbError(
          err instanceof Error ? err.message : 'Hugging Face Parquet への接続に失敗しました',
        );
      });

    return () => {
      cancelled = true;
    };
  }, []);

  useEffect(() => {
    writeHashState(activeTab, selectedLawId, selectedArticleNum);
  }, [activeTab, selectedLawId, selectedArticleNum]);

  useEffect(() => {
    const onHashChange = () => {
      const parsed = parseHashState();
      setActiveTab(parsed.tab);
      if (parsed.lawId) setSelectedLawId(parsed.lawId);
      if (parsed.articleNum) setSelectedArticleNum(parsed.articleNum);
    };
    window.addEventListener('hashchange', onHashChange);
    return () => window.removeEventListener('hashchange', onHashChange);
  }, []);

  const handleSelectLaw = useCallback((lawId: string, articleNum?: string) => {
    setSelectedLawId(lawId);
    setSelectedArticleNum(articleNum ?? null);
  }, []);

  const handleOpenInGraph = useCallback((lawId: string, articleNum?: string) => {
    setSelectedLawId(lawId);
    if (articleNum) setSelectedArticleNum(articleNum);
    setActiveTab('graph');
  }, []);

  const handleOpenInViewer = useCallback((lawId: string, articleNum?: string) => {
    setSelectedLawId(lawId);
    setSelectedArticleNum(articleNum ?? null);
    setActiveTab('viewer');
  }, []);

  return (
    <div className="app-shell">
      <header className="app-header">
        <div className="brand">
          <div className="brand-icon">
            <Scale size={18} />
          </div>
          <div>
            <h1 className="brand-title">日本法令 Explorer</h1>
            <p className="brand-sub">Hugging Face Parquet × DuckDB-Wasm 静的ビューワー＆分析</p>
          </div>
        </div>

        <nav className="tab-nav" aria-label="メインナビゲーション">
          <button
            type="button"
            className={`tab-btn ${activeTab === 'viewer' ? 'active' : ''}`}
            onClick={() => setActiveTab('viewer')}
          >
            <BookOpen size={15} />
            条文ビューワー
          </button>
          <button
            type="button"
            className={`tab-btn ${activeTab === 'graph' ? 'active' : ''}`}
            onClick={() => setActiveTab('graph')}
          >
            <Network size={15} />
            参照ネットワーク
          </button>
          <button
            type="button"
            className={`tab-btn ${activeTab === 'analytics' ? 'active' : ''}`}
            onClick={() => setActiveTab('analytics')}
          >
            <BarChart3 size={15} />
            アナリティクス & SQL
          </button>
        </nav>

        <div className="header-meta">
          <span className={`status-pill ${dbStatus}`}>
            <span className="status-dot" />
            {dbStatus === 'initializing' && 'DuckDB-Wasm 接続中...'}
            {dbStatus === 'ready' && `HF Parquet 接続済 (${catalog.length} 法令)`}
            {dbStatus === 'error' && '接続エラー'}
          </span>
          <a
            className="header-link"
            href={HF_DATASET_URL}
            target="_blank"
            rel="noopener noreferrer"
          >
            Dataset
            <ExternalLink size={12} />
          </a>
          <a
            className="header-link"
            href={GITHUB_REPO_URL}
            target="_blank"
            rel="noopener noreferrer"
          >
            GitHub
            <ExternalLink size={12} />
          </a>
        </div>
      </header>

      <main className="app-main">
        {dbStatus === 'error' ? (
          <div className="analytics-scroll">
            <div className="analytics-container">
              <div className="error-banner">
                データセットの読み込みに失敗しました: {dbError}
              </div>
            </div>
          </div>
        ) : dbStatus === 'initializing' ? (
          <div className="empty-state" style={{ marginTop: '4rem' }}>
            ブラウザ内で DuckDB-Wasm を起動し、Hugging Face Datasets（Chottokun/japan-laws-md）のインデックスを読み込んでいます...
          </div>
        ) : (
          <>
            {activeTab === 'viewer' && (
              <ViewerTab
                catalog={catalog}
                selectedLawId={selectedLawId}
                selectedArticleNum={selectedArticleNum}
                onSelectLaw={handleSelectLaw}
                onSelectArticle={setSelectedArticleNum}
                onOpenInGraph={handleOpenInGraph}
                onNotify={notify}
              />
            )}
            {activeTab === 'graph' && (
              <GraphTab
                catalog={catalog}
                selectedLawId={selectedLawId}
                selectedArticleNum={selectedArticleNum}
                onSelectLaw={handleSelectLaw}
                onOpenInViewer={handleOpenInViewer}
              />
            )}
            {activeTab === 'analytics' && (
              <AnalyticsTab onOpenLawInViewer={handleOpenInViewer} onNotify={notify} />
            )}
          </>
        )}
      </main>

      {toasts.length > 0 && (
        <div className="toast-stack" role="status" aria-live="polite">
          {toasts.map((toast) => (
            <div key={toast.id} className={`toast ${toast.kind}`}>
              {toast.text}
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
export default App;
