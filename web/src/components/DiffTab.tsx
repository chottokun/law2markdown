import { ArrowLeftRight, BookOpen, GitCompare, Search } from 'lucide-react';
import { useEffect, useMemo, useState } from 'react';
import {
  computeArticleDiffList,
  computeLineDiff,
  findMultiVersionLaws,
  parseLawVersionLabel,
  type ArticleDiffKind,
} from '../lib/diffUtils';
import { fetchLawArticlesWithContent } from '../lib/queries';
import type { ArticleContentRow, LawCatalogEntry } from '../lib/types';

interface DiffTabProps {
  catalog: LawCatalogEntry[];
  onOpenInViewer: (lawId: string, articleNum?: string) => void;
  onNotify: (kind: 'info' | 'success' | 'error', text: string) => void;
}

const KIND_LABELS: Record<ArticleDiffKind, string> = {
  modified: '変更',
  added: '新設',
  removed: '削除',
};

export function DiffTab({ catalog, onOpenInViewer, onNotify }: DiffTabProps) {
  const multiVersionLaws = useMemo(() => findMultiVersionLaws(catalog), [catalog]);

  const [lawFilter, setLawFilter] = useState('');
  const [selectedBaseKey, setSelectedBaseKey] = useState<string | null>(
    multiVersionLaws[0]?.baseKey ?? null,
  );
  const [oldLawId, setOldLawId] = useState<string>('');
  const [newLawId, setNewLawId] = useState<string>('');

  const [oldArticles, setOldArticles] = useState<ArticleContentRow[]>([]);
  const [newArticles, setNewArticles] = useState<ArticleContentRow[]>([]);
  const [loading, setLoading] = useState(false);

  const [kindFilter, setKindFilter] = useState<'all' | ArticleDiffKind>('all');
  const [selectedArticleNum, setSelectedArticleNum] = useState<string | null>(null);

  const selectedGroup = useMemo(
    () => multiVersionLaws.find((g) => g.baseKey === selectedBaseKey) ?? multiVersionLaws[0] ?? null,
    [multiVersionLaws, selectedBaseKey],
  );

  // 選択法令が変わったらデフォルトで最古版 vs 最新版を選択
  useEffect(() => {
    if (!selectedGroup) return;
    if (selectedBaseKey !== selectedGroup.baseKey) {
      setSelectedBaseKey(selectedGroup.baseKey);
    }
    const versions = selectedGroup.versions;
    setOldLawId(versions[0].law_id);
    setNewLawId(versions[versions.length - 1].law_id);
  }, [selectedGroup?.baseKey]);

  useEffect(() => {
    if (!oldLawId || !newLawId) return;
    let cancelled = false;
    setLoading(true);
    Promise.all([fetchLawArticlesWithContent(oldLawId), fetchLawArticlesWithContent(newLawId)])
      .then(([oldRes, newRes]) => {
        if (cancelled) return;
        setOldArticles(oldRes);
        setNewArticles(newRes);
      })
      .catch((err) => {
        if (!cancelled) {
          onNotify('error', err instanceof Error ? err.message : '比較データの取得に失敗しました');
        }
      })
      .finally(() => {
        if (!cancelled) setLoading(false);
      });

    return () => {
      cancelled = true;
    };
  }, [oldLawId, newLawId]);

  const diffSummary = useMemo(
    () => computeArticleDiffList(oldArticles, newArticles),
    [oldArticles, newArticles],
  );

  const visibleItems = useMemo(() => {
    if (kindFilter === 'all') return diffSummary.items;
    return diffSummary.items.filter((item) => item.kind === kindFilter);
  }, [diffSummary.items, kindFilter]);

  useEffect(() => {
    if (visibleItems.length === 0) {
      setSelectedArticleNum(null);
      return;
    }
    if (!selectedArticleNum || !visibleItems.some((i) => i.article_num === selectedArticleNum)) {
      setSelectedArticleNum(visibleItems[0].article_num);
    }
  }, [visibleItems, selectedArticleNum]);

  const activeItem = useMemo(
    () => visibleItems.find((i) => i.article_num === selectedArticleNum) ?? null,
    [visibleItems, selectedArticleNum],
  );

  const diffLines = useMemo(() => {
    if (!activeItem) return [];
    return computeLineDiff(activeItem.oldContent, activeItem.newContent);
  }, [activeItem]);

  const filteredGroups = useMemo(() => {
    const q = lawFilter.trim().toLowerCase();
    const matched = q
      ? multiVersionLaws.filter(
          (g) =>
            g.lawTitle.toLowerCase().includes(q) || g.lawNum.toLowerCase().includes(q),
        )
      : multiVersionLaws;
    return matched.slice(0, 150);
  }, [multiVersionLaws, lawFilter]);

  if (multiVersionLaws.length === 0) {
    return (
      <div className="empty-state" style={{ marginTop: '3rem' }}>
        <GitCompare size={32} style={{ opacity: 0.5, marginBottom: '0.5rem' }} />
        <div>複数バージョンが収録されている法令が見つかりませんでした。</div>
      </div>
    );
  }

  return (
    <div className="diff-shell">
      {/* 左ペイン: 複数バージョンがある法令一覧 */}
      <aside className="pane">
        <div className="pane-header">
          <div style={{ fontSize: '0.84rem', fontWeight: 600 }}>
            複数版収録法令 ({multiVersionLaws.length} 件)
          </div>
          <div className="input-box">
            <Search size={14} color="#94a3b8" />
            <input
              type="text"
              placeholder="法令名で絞込..."
              value={lawFilter}
              onChange={(e) => setLawFilter(e.target.value)}
            />
          </div>
        </div>
        <div className="pane-scroll">
          {filteredGroups.map((group) => (
            <button
              key={group.baseKey}
              type="button"
              className={`list-item ${selectedGroup?.baseKey === group.baseKey ? 'active' : ''}`}
              onClick={() => setSelectedBaseKey(group.baseKey)}
            >
              <span className="list-item-title">{group.lawTitle}</span>
              <span className="list-item-meta">
                <span>{group.lawNum}</span>
                <span>{group.versions.length} 版</span>
              </span>
            </button>
          ))}
        </div>
      </aside>

      {/* 右側: バージョン選択バー + 変更条文一覧 + Diffビュー */}
      <div className="diff-workspace">
        <div className="diff-toolbar">
          <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', flexWrap: 'wrap' }}>
            <label style={{ fontSize: '0.8rem', color: '#94a3b8' }}>
              旧版:
              <select
                aria-label="旧版"
                className="select-box"
                style={{ marginLeft: '0.35rem' }}
                value={oldLawId}
                onChange={(e) => setOldLawId(e.target.value)}
              >
                {selectedGroup?.versions.map((v) => (
                  <option key={v.law_id} value={v.law_id}>
                    {parseLawVersionLabel(v.law_id)} ({v.article_count}条)
                  </option>
                ))}
              </select>
            </label>

            <button
              type="button"
              className="btn"
              title="旧版と新版を入れ替え"
              onClick={() => {
                setOldLawId(newLawId);
                setNewLawId(oldLawId);
              }}
            >
              <ArrowLeftRight size={14} />
            </button>

            <label style={{ fontSize: '0.8rem', color: '#94a3b8' }}>
              新版:
              <select
                aria-label="新版"
                className="select-box"
                style={{ marginLeft: '0.35rem' }}
                value={newLawId}
                onChange={(e) => setNewLawId(e.target.value)}
              >
                {selectedGroup?.versions.map((v) => (
                  <option key={v.law_id} value={v.law_id}>
                    {parseLawVersionLabel(v.law_id)} ({v.article_count}条)
                  </option>
                ))}
              </select>
            </label>
          </div>

          <div className="chip-row">
            <button
              type="button"
              className={`chip ${kindFilter === 'all' ? 'active' : ''}`}
              onClick={() => setKindFilter('all')}
            >
              差分計 {diffSummary.items.length}
            </button>
            <button
              type="button"
              className={`chip ${kindFilter === 'modified' ? 'amber' : ''}`}
              onClick={() => setKindFilter('modified')}
            >
              変更 {diffSummary.modifiedCount}
            </button>
            <button
              type="button"
              className={`chip ${kindFilter === 'added' ? 'emerald' : ''}`}
              onClick={() => setKindFilter('added')}
            >
              新設 {diffSummary.addedCount}
            </button>
            <button
              type="button"
              className={`chip ${kindFilter === 'removed' ? 'active' : ''}`}
              onClick={() => setKindFilter('removed')}
            >
              削除 {diffSummary.removedCount}
            </button>
            <span className="chip">変更なし {diffSummary.unchangedCount}</span>
          </div>
        </div>

        <div className="diff-split">
          <div className="pane" style={{ borderRight: '1px solid var(--border-subtle)' }}>
            <div className="pane-scroll">
              {loading ? (
                <div className="empty-state">新旧バージョンを比較中...</div>
              ) : visibleItems.length === 0 ? (
                <div className="empty-state">選択したバージョン間に条文本文の差分はありません</div>
              ) : (
                visibleItems.map((item) => (
                  <button
                    key={item.article_num}
                    type="button"
                    className={`list-item ${
                      selectedArticleNum === item.article_num ? 'active' : ''
                    }`}
                    onClick={() => setSelectedArticleNum(item.article_num)}
                  >
                    <span className="list-item-title">
                      {item.title.replace(/^[^\s]+\s+/, '') || `第${item.article_num}条`}
                    </span>
                    <span className="list-item-meta">
                      <span className={`diff-badge ${item.kind}`}>{KIND_LABELS[item.kind]}</span>
                      <span>第{item.article_num}条</span>
                    </span>
                  </button>
                ))
              )}
            </div>
          </div>

          <div className="reader-scroll">
            {loading ? (
              <div className="empty-state">読み込み中...</div>
            ) : !activeItem ? (
              <div className="empty-state">比較する条文を選択してください</div>
            ) : (
              <div className="reader-card">
                <div className="reader-breadcrumb">{activeItem.hierarchy_path}</div>
                <div className="reader-toolbar">
                  <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
                    <span className={`diff-badge ${activeItem.kind}`}>
                      {KIND_LABELS[activeItem.kind]}
                    </span>
                    <strong>{activeItem.title}</strong>
                  </div>
                  <div style={{ display: 'flex', gap: '0.45rem', flexWrap: 'wrap' }}>
                    {activeItem.kind !== 'added' && (
                      <button
                        type="button"
                        className="btn"
                        onClick={() => onOpenInViewer(oldLawId, activeItem.article_num)}
                      >
                        <BookOpen size={14} />
                        旧版を開く
                      </button>
                    )}
                    {activeItem.kind !== 'removed' && (
                      <button
                        type="button"
                        className="btn primary"
                        onClick={() => onOpenInViewer(newLawId, activeItem.article_num)}
                      >
                        <BookOpen size={14} />
                        新版を開く
                      </button>
                    )}
                  </div>
                </div>

                <div className="diff-view" role="region" aria-label="条文差分">
                  {diffLines.map((line, idx) => (
                    <div key={idx} className={`diff-line ${line.type}`}>
                      <span className="diff-prefix">
                        {line.type === 'added' ? '+' : line.type === 'removed' ? '-' : ' '}
                      </span>
                      <span className="diff-text">{line.text || ' '}</span>
                    </div>
                  ))}
                </div>
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}
