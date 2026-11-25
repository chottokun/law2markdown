import {
  BookOpen,
  ChevronDown,
  ChevronRight,
  Copy,
  Network,
  Search,
} from 'lucide-react';
import { useEffect, useMemo, useState } from 'react';
import { CORE_LAWS } from '../lib/constants';
import { parseRefArticleKey } from '../lib/graphBuilder';
import { buildHierarchyTree, type HierarchyNode } from '../lib/hierarchyTree';
import { fetchArticleDetail, fetchLawArticles, searchArticles } from '../lib/queries';
import { renderSafeMarkdown, stripHtmlTags } from '../lib/sanitize';
import type {
  ArticleDetail,
  ArticleSummary,
  LawCatalogEntry,
  SearchResultEntry,
} from '../lib/types';

interface ViewerTabProps {
  catalog: LawCatalogEntry[];
  selectedLawId: string | null;
  selectedArticleNum: string | null;
  onSelectLaw: (lawId: string, articleNum?: string) => void;
  onSelectArticle: (articleNum: string) => void;
  onOpenInGraph: (lawId: string, articleNum?: string) => void;
  onNotify: (kind: 'info' | 'success' | 'error', text: string) => void;
}

interface TreeBranchProps {
  node: HierarchyNode;
  selectedArticleNum: string | null;
  expandedIds: Set<string>;
  onToggle: (id: string) => void;
  onSelectArticle: (articleNum: string) => void;
}

function TreeBranch({
  node,
  selectedArticleNum,
  expandedIds,
  onToggle,
  onSelectArticle,
}: TreeBranchProps) {
  const isExpanded = expandedIds.has(node.id);
  return (
    <div>
      <button
        type="button"
        className="tree-group-btn"
        onClick={() => onToggle(node.id)}
      >
        {isExpanded ? <ChevronDown size={14} /> : <ChevronRight size={14} />}
        <span>{node.label}</span>
      </button>
      {isExpanded && (
        <div className="tree-children">
          {node.children.map((child) => (
            <TreeBranch
              key={child.id}
              node={child}
              selectedArticleNum={selectedArticleNum}
              expandedIds={expandedIds}
              onToggle={onToggle}
              onSelectArticle={onSelectArticle}
            />
          ))}
          {node.articles.map((art) => (
            <button
              key={art.article_num}
              type="button"
              className={`tree-article-btn ${
                selectedArticleNum === art.article_num ? 'active' : ''
              }`}
              title={art.title}
              onClick={() => onSelectArticle(art.article_num)}
            >
              {art.title.replace(/^[^\s]+\s+/, '') || `第${art.article_num}条`}
            </button>
          ))}
        </div>
      )}
    </div>
  );
}

export function ViewerTab({
  catalog,
  selectedLawId,
  selectedArticleNum,
  onSelectLaw,
  onSelectArticle,
  onOpenInGraph,
  onNotify,
}: ViewerTabProps) {
  const [sidebarMode, setSidebarMode] = useState<'laws' | 'search'>('laws');
  const [lawFilter, setLawFilter] = useState('');
  const [tocFilter, setTocFilter] = useState('');

  const [articles, setArticles] = useState<ArticleSummary[]>([]);
  const [articlesLoading, setArticlesLoading] = useState(false);

  const [detail, setDetail] = useState<ArticleDetail | null>(null);
  const [detailLoading, setDetailLoading] = useState(false);

  const [searchKeyword, setSearchKeyword] = useState('');
  const [searchResults, setSearchResults] = useState<SearchResultEntry[]>([]);
  const [searching, setSearching] = useState(false);

  const [expandedIds, setExpandedIds] = useState<Set<string>>(new Set(['本則']));

  const filteredLaws = useMemo(() => {
    const q = lawFilter.trim().toLowerCase();
    const matched = q
      ? catalog.filter(
          (l) =>
            l.law_title.toLowerCase().includes(q) ||
            l.law_num.toLowerCase().includes(q) ||
            l.law_id.toLowerCase().includes(q),
        )
      : catalog;
    return matched.slice(0, 200);
  }, [catalog, lawFilter]);

  const filteredArticles = useMemo(() => {
    const q = tocFilter.trim().toLowerCase();
    if (!q) return articles;
    return articles.filter(
      (a) =>
        a.title.toLowerCase().includes(q) ||
        a.article_num.toLowerCase().includes(q) ||
        a.hierarchy_path.toLowerCase().includes(q),
    );
  }, [articles, tocFilter]);

  const tree = useMemo(() => buildHierarchyTree(filteredArticles), [filteredArticles]);

  const articleNumSet = useMemo(
    () => new Set(articles.map((a) => a.article_num)),
    [articles],
  );

  // 法令切替時に条文メタデータ一覧を取得
  useEffect(() => {
    if (!selectedLawId) {
      setArticles([]);
      return;
    }
    let cancelled = false;
    setArticlesLoading(true);
    fetchLawArticles(selectedLawId)
      .then((list) => {
        if (cancelled) return;
        setArticles(list);
        const defaultExpand = new Set<string>();
        const firstTree = buildHierarchyTree(list);
        if (firstTree.children[0]) {
          defaultExpand.add(firstTree.children[0].id);
        }
        setExpandedIds(defaultExpand);

        if (list.length > 0) {
          const exists =
            selectedArticleNum && list.some((a) => a.article_num === selectedArticleNum);
          if (!exists) {
            onSelectArticle(list[0].article_num);
          }
        }
      })
      .catch((err) => {
        if (!cancelled) {
          onNotify('error', err instanceof Error ? err.message : '条文一覧の取得に失敗しました');
        }
      })
      .finally(() => {
        if (!cancelled) setArticlesLoading(false);
      });

    return () => {
      cancelled = true;
    };
  }, [selectedLawId]);

  // 選択中条文の本文を取得
  useEffect(() => {
    if (!selectedLawId || !selectedArticleNum) {
      setDetail(null);
      return;
    }
    let cancelled = false;
    setDetailLoading(true);
    fetchArticleDetail(selectedLawId, selectedArticleNum)
      .then((res) => {
        if (!cancelled) setDetail(res);
      })
      .catch((err) => {
        if (!cancelled) {
          onNotify('error', err instanceof Error ? err.message : '条文本文の取得に失敗しました');
        }
      })
      .finally(() => {
        if (!cancelled) setDetailLoading(false);
      });

    return () => {
      cancelled = true;
    };
  }, [selectedLawId, selectedArticleNum]);

  // 選択条文を含むフォルダを自動展開
  useEffect(() => {
    if (!selectedArticleNum || articles.length === 0) return;
    const current = articles.find((a) => a.article_num === selectedArticleNum);
    if (!current) return;
    const segments = current.hierarchy_path
      .split(' > ')
      .map((s) => s.trim())
      .filter(Boolean);
    const folderSegments = segments.length > 2 ? segments.slice(1, -1) : ['本則'];
    setExpandedIds((prev) => {
      const next = new Set(prev);
      let acc = '';
      for (const seg of folderSegments) {
        acc = acc ? `${acc} > ${seg}` : seg;
        next.add(acc);
      }
      return next;
    });
  }, [selectedArticleNum, articles]);

  const handleToggleFolder = (id: string) => {
    setExpandedIds((prev) => {
      const next = new Set(prev);
      if (next.has(id)) next.delete(id);
      else next.add(id);
      return next;
    });
  };

  const handleCoreLawClick = (idPrefix: string, title: string) => {
    const match =
      catalog.find((l) => l.law_id.startsWith(idPrefix)) ??
      catalog.find((l) => l.law_title === title);
    if (match) {
      onSelectLaw(match.law_id);
    } else {
      onNotify('info', `「${title}」は現在のデータセットに見つかりませんでした。`);
    }
  };

  const handleSearchSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    const q = searchKeyword.trim();
    if (!q) return;
    setSearching(true);
    try {
      const rows = await searchArticles(q, 50);
      setSearchResults(rows);
      if (rows.length === 0) {
        onNotify('info', `「${q}」に一致する条文は見つかりませんでした。`);
      }
    } catch (err) {
      onNotify('error', err instanceof Error ? err.message : '検索に失敗しました');
    } finally {
      setSearching(false);
    }
  };

  const handleCopyRagContext = async () => {
    if (!detail) return;
    const cleanText = stripHtmlTags(detail.content);
    const promptText = [
      `## ${detail.law_title}（${detail.law_num}）`,
      `- 階層: ${detail.hierarchy_path}`,
      `- 条文ID: ${detail.law_id} / 第${detail.article_num}条`,
      '',
      cleanText,
    ].join('\n');

    try {
      await navigator.clipboard.writeText(promptText);
      onNotify('success', 'RAG プロンプト用テキストをクリップボードにコピーしました');
    } catch {
      onNotify('error', 'クリップボードへのコピーに失敗しました');
    }
  };

  // DOMPurify.sanitize() によるサニタイズ済み HTML のみを生成
  const sanitizedHtml = useMemo(
    () => (detail ? renderSafeMarkdown(detail.content) : ''),
    [detail],
  );

  return (
    <div className="viewer-grid">
      {/* 左ペイン: 法令一覧 / 全文横断検索 */}
      <aside className="pane">
        <div className="pane-header">
          <div className="segmented">
            <button
              type="button"
              className={sidebarMode === 'laws' ? 'active' : ''}
              onClick={() => setSidebarMode('laws')}
            >
              法令一覧 ({catalog.length})
            </button>
            <button
              type="button"
              className={sidebarMode === 'search' ? 'active' : ''}
              onClick={() => setSidebarMode('search')}
            >
              全法令検索
            </button>
          </div>

          {sidebarMode === 'laws' ? (
            <>
              <div className="input-box">
                <Search size={14} color="#94a3b8" />
                <input
                  type="text"
                  placeholder="法令名・法令番号で絞込..."
                  value={lawFilter}
                  onChange={(e) => setLawFilter(e.target.value)}
                />
              </div>
              <div className="chip-row">
                {CORE_LAWS.slice(0, 8).map((core) => (
                  <button
                    key={core.idPrefix}
                    type="button"
                    className={`chip ${
                      selectedLawId?.startsWith(core.idPrefix) ? 'active' : ''
                    }`}
                    onClick={() => handleCoreLawClick(core.idPrefix, core.title)}
                  >
                    {core.label}
                  </button>
                ))}
              </div>
            </>
          ) : (
            <form onSubmit={handleSearchSubmit} style={{ display: 'flex', gap: '0.4rem' }}>
              <div className="input-box" style={{ flex: 1 }}>
                <Search size={14} color="#94a3b8" />
                <input
                  type="text"
                  placeholder="例: 損害賠償, 個人情報..."
                  value={searchKeyword}
                  onChange={(e) => setSearchKeyword(e.target.value)}
                />
              </div>
              <button type="submit" className="btn primary" disabled={searching}>
                {searching ? '検索中' : '検索'}
              </button>
            </form>
          )}
        </div>

        <div className="pane-scroll">
          {sidebarMode === 'laws' ? (
            filteredLaws.length === 0 ? (
              <div className="empty-state">該当する法令がありません</div>
            ) : (
              <>
                {filteredLaws.map((law) => (
                  <button
                    key={law.law_id}
                    type="button"
                    className={`list-item ${selectedLawId === law.law_id ? 'active' : ''}`}
                    onClick={() => onSelectLaw(law.law_id)}
                  >
                    <span className="list-item-title">{law.law_title}</span>
                    <span className="list-item-meta">
                      <span>{law.law_num}</span>
                      <span>{law.article_count} 条</span>
                    </span>
                  </button>
                ))}
                {catalog.length > 200 && !lawFilter.trim() && (
                  <div className="empty-state" style={{ padding: '0.75rem', fontSize: '0.75rem' }}>
                    上位 200 件を表示中（全 {catalog.length} 件は検索で絞込）
                  </div>
                )}
              </>
            )
          ) : searchResults.length === 0 ? (
            <div className="empty-state">
              キーワードを入力して全 {catalog.length} 法令を横断検索できます
            </div>
          ) : (
            searchResults.map((hit) => (
              <button
                key={`${hit.law_id}-${hit.article_num}`}
                type="button"
                className="list-item"
                onClick={() => onSelectLaw(hit.law_id, hit.article_num)}
              >
                <span className="list-item-title">{hit.title}</span>
                <span className="list-item-meta">
                  <span>{hit.law_num}</span>
                </span>
                <span style={{ fontSize: '0.75rem', color: '#94a3b8', marginTop: '0.2rem' }}>
                  {hit.snippet}...
                </span>
              </button>
            ))
          )}
        </div>
      </aside>

      {/* 中ペイン: 階層ツリー目次 */}
      <aside className="pane">
        <div className="pane-header">
          <div style={{ fontSize: '0.82rem', fontWeight: 600 }}>
            条文ツリー ({articles.length} 条)
          </div>
          <div className="input-box">
            <Search size={14} color="#94a3b8" />
            <input
              type="text"
              placeholder="条文番号・見出しで絞込..."
              value={tocFilter}
              onChange={(e) => setTocFilter(e.target.value)}
            />
          </div>
        </div>

        <div className="pane-scroll">
          {articlesLoading ? (
            <div className="empty-state">条文一覧を読み込み中...</div>
          ) : tree.children.length === 0 ? (
            <div className="empty-state">法令を選択してください</div>
          ) : (
            tree.children.map((child) => (
              <TreeBranch
                key={child.id}
                node={child}
                selectedArticleNum={selectedArticleNum}
                expandedIds={expandedIds}
                onToggle={handleToggleFolder}
                onSelectArticle={onSelectArticle}
              />
            ))
          )}
        </div>
      </aside>

      {/* 右ペイン: 条文本文リーダー */}
      <section className="pane">
        <div className="reader-scroll">
          {detailLoading ? (
            <div className="empty-state">条文データを取得中...</div>
          ) : !detail ? (
            <div className="empty-state">
              <BookOpen size={32} style={{ opacity: 0.5, marginBottom: '0.5rem' }} />
              <div>左のリストから法令・条文を選択してください</div>
            </div>
          ) : (
            <article className="reader-card">
              <div className="reader-breadcrumb">
                {detail.hierarchy_path} ・ {detail.law_num}
              </div>

              <div className="reader-toolbar">
                <div className="chip-row">
                  {detail.defined_terms.map((term) => (
                    <span key={term} className="chip emerald">
                      定義: {term}
                    </span>
                  ))}
                </div>
                <div style={{ display: 'flex', gap: '0.5rem' }}>
                  <button type="button" className="btn" onClick={handleCopyRagContext}>
                    <Copy size={14} />
                    RAG用にコピー
                  </button>
                  <button
                    type="button"
                    className="btn primary"
                    onClick={() => onOpenInGraph(detail.law_id, detail.article_num)}
                  >
                    <Network size={14} />
                    参照グラフで見る
                  </button>
                </div>
              </div>

              {/* DOMPurify.sanitize によりサニタイズ済みの HTML のみ挿入する */}
              <div
                className="markdown-body"
                dangerouslySetInnerHTML={{ __html: sanitizedHtml }}
              />

              <div className="refs-panel">
                <div>
                  <h4>この条文が参照している条文 ({detail.outbound_references.length})</h4>
                  {detail.outbound_references.length === 0 ? (
                    <span style={{ fontSize: '0.8rem', color: '#64748b' }}>なし</span>
                  ) : (
                    <div className="chip-row">
                      {detail.outbound_references.map((ref) => {
                        const target = parseRefArticleKey(ref);
                        const clickable = target && articleNumSet.has(target);
                        return (
                          <button
                            key={ref}
                            type="button"
                            className={`chip ${clickable ? 'active' : ''}`}
                            disabled={!clickable}
                            onClick={() => target && onSelectArticle(target)}
                          >
                            {ref}
                          </button>
                        );
                      })}
                    </div>
                  )}
                </div>

                <div>
                  <h4>この条文を参照している条文 ({detail.inbound_references.length})</h4>
                  {detail.inbound_references.length === 0 ? (
                    <span style={{ fontSize: '0.8rem', color: '#64748b' }}>なし</span>
                  ) : (
                    <div className="chip-row">
                      {detail.inbound_references.map((ref) => {
                        const target = parseRefArticleKey(ref);
                        const clickable = target && articleNumSet.has(target);
                        return (
                          <button
                            key={ref}
                            type="button"
                            className={`chip ${clickable ? 'amber' : ''}`}
                            disabled={!clickable}
                            onClick={() => target && onSelectArticle(target)}
                          >
                            {ref}
                          </button>
                        );
                      })}
                    </div>
                  )}
                </div>
              </div>
            </article>
          )}
        </div>
      </section>
    </div>
  );
}
