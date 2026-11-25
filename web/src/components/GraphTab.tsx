import cytoscape, { type Core, type NodeSingular } from 'cytoscape';
import { BookOpen, Maximize2, Search } from 'lucide-react';
import { useEffect, useMemo, useRef, useState } from 'react';
import { CORE_LAWS } from '../lib/constants';
import { buildLawGraphElements, parseRefArticleKey } from '../lib/graphBuilder';
import { fetchLawArticles } from '../lib/queries';
import type { ArticleSummary, LawCatalogEntry } from '../lib/types';

interface GraphTabProps {
  catalog: LawCatalogEntry[];
  selectedLawId: string | null;
  selectedArticleNum: string | null;
  onSelectLaw: (lawId: string, articleNum?: string) => void;
  onOpenInViewer: (lawId: string, articleNum: string) => void;
}

type LayoutKind = 'cose' | 'concentric' | 'breadthfirst';

export function GraphTab({
  catalog,
  selectedLawId,
  selectedArticleNum,
  onSelectLaw,
  onOpenInViewer,
}: GraphTabProps) {
  const containerRef = useRef<HTMLDivElement | null>(null);
  const cyRef = useRef<Core | null>(null);

  const [articles, setArticles] = useState<ArticleSummary[]>([]);
  const [loading, setLoading] = useState(false);
  const [layoutKind, setLayoutKind] = useState<LayoutKind>('cose');
  const [nodeSearch, setNodeSearch] = useState('');
  const [focusedArticleNum, setFocusedArticleNum] = useState<string | null>(selectedArticleNum);

  useEffect(() => {
    setFocusedArticleNum(selectedArticleNum);
  }, [selectedArticleNum]);

  useEffect(() => {
    if (!selectedLawId) {
      setArticles([]);
      return;
    }
    let cancelled = false;
    setLoading(true);
    fetchLawArticles(selectedLawId)
      .then((list) => {
        if (!cancelled) setArticles(list);
      })
      .finally(() => {
        if (!cancelled) setLoading(false);
      });
    return () => {
      cancelled = true;
    };
  }, [selectedLawId]);

  const graph = useMemo(() => buildLawGraphElements(articles), [articles]);

  const selectorLaws = useMemo(() => {
    const top = catalog.slice(0, 150);
    if (selectedLawId && !top.some((l) => l.law_id === selectedLawId)) {
      const current = catalog.find((l) => l.law_id === selectedLawId);
      if (current) return [current, ...top];
    }
    return top;
  }, [catalog, selectedLawId]);

  const focusedArticle = useMemo(
    () => articles.find((a) => a.article_num === focusedArticleNum) ?? null,
    [articles, focusedArticleNum],
  );

  const highlightNode = (cy: Core, node: NodeSingular) => {
    cy.elements().removeClass('faded active-node out-neighbor in-neighbor active-edge');
    const outgoers = node.outgoers();
    const incomers = node.incomers();
    const neighborhood = node.closedNeighborhood();

    cy.elements().difference(neighborhood).addClass('faded');
    node.addClass('active-node');
    outgoers.nodes().addClass('out-neighbor');
    incomers.nodes().addClass('in-neighbor');
    outgoers.edges().addClass('active-edge');
    incomers.edges().addClass('active-edge');
  };

  useEffect(() => {
    const container = containerRef.current;
    if (!container || graph.nodes.length === 0) {
      cyRef.current?.destroy();
      cyRef.current = null;
      return;
    }

    const animate = graph.nodes.length <= 220;
    const cy = cytoscape({
      container,
      elements: [...graph.nodes, ...graph.edges],
      style: [
        {
          selector: 'node',
          style: {
            width: 'data(size)',
            height: 'data(size)',
            label: 'data(label)',
            'font-size': 10,
            color: '#e2e8f0',
            'text-valign': 'bottom',
            'text-margin-y': 5,
            'background-color': '#38bdf8',
            'border-width': 1.5,
            'border-color': '#0ea5e9',
          },
        },
        {
          selector: 'edge',
          style: {
            width: 1.3,
            'line-color': '#334155',
            'target-arrow-color': '#475569',
            'target-arrow-shape': 'triangle',
            'curve-style': 'bezier',
            opacity: 0.65,
          },
        },
        {
          selector: '.faded',
          style: {
            opacity: 0.14,
          },
        },
        {
          selector: '.active-node',
          style: {
            'background-color': '#ffffff',
            'border-color': '#38bdf8',
            'border-width': 3,
          },
        },
        {
          selector: '.out-neighbor',
          style: {
            'background-color': '#38bdf8',
            'border-color': '#bae6fd',
            'border-width': 2.5,
          },
        },
        {
          selector: '.in-neighbor',
          style: {
            'background-color': '#f59e0b',
            'border-color': '#fde68a',
            'border-width': 2.5,
          },
        },
        {
          selector: '.active-edge',
          style: {
            'line-color': '#38bdf8',
            'target-arrow-color': '#38bdf8',
            width: 2.2,
            opacity: 1,
          },
        },
      ],
      layout:
        layoutKind === 'concentric'
          ? {
              name: 'concentric',
              animate,
              concentric: (node) => Number(node.data('inDegree') ?? 0),
              levelWidth: () => 2,
            }
          : layoutKind === 'breadthfirst'
            ? {
                name: 'breadthfirst',
                directed: true,
                animate,
                padding: 24,
              }
            : {
                name: 'cose',
                animate,
                nodeRepulsion: () => 4500,
                idealEdgeLength: () => 90,
                padding: 24,
              },
    });

    cy.on('tap', 'node', (evt) => {
      const node = evt.target as NodeSingular;
      setFocusedArticleNum(node.id());
      highlightNode(cy, node);
    });

    cy.on('tap', (evt) => {
      if (evt.target === cy) {
        cy.elements().removeClass('faded active-node out-neighbor in-neighbor active-edge');
      }
    });

    if (focusedArticleNum) {
      const targetNode = cy.getElementById(focusedArticleNum);
      if (targetNode.nonempty()) {
        highlightNode(cy, targetNode as NodeSingular);
      }
    }

    cyRef.current = cy;
    return () => {
      cy.destroy();
      cyRef.current = null;
    };
  }, [graph, layoutKind]);

  const handleFocusNodeByQuery = (e: React.FormEvent) => {
    e.preventDefault();
    const cy = cyRef.current;
    const q = nodeSearch.trim().toLowerCase();
    if (!cy || !q) return;

    const hit = articles.find(
      (a) =>
        a.article_num.toLowerCase() === q ||
        a.title.toLowerCase().includes(q) ||
        `第${a.article_num}条`.includes(q),
    );
    if (!hit) return;

    const node = cy.getElementById(hit.article_num);
    if (node.nonempty()) {
      setFocusedArticleNum(hit.article_num);
      highlightNode(cy, node as NodeSingular);
      cy.animate({ center: { eles: node }, zoom: 1.4, duration: 300 });
    }
  };

  const handleCoreLawClick = (idPrefix: string, title: string) => {
    const match =
      catalog.find((l) => l.law_id.startsWith(idPrefix)) ??
      catalog.find((l) => l.law_title === title);
    if (match) {
      onSelectLaw(match.law_id);
    }
  };

  const articleNumSet = useMemo(() => new Set(articles.map((a) => a.article_num)), [articles]);

  return (
    <div className="graph-layout">
      <div className="graph-main">
        <div className="graph-toolbar">
          <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', flexWrap: 'wrap' }}>
            <select
              className="select-box"
              value={selectedLawId ?? ''}
              onChange={(e) => onSelectLaw(e.target.value)}
            >
              {selectorLaws.map((law) => (
                <option key={law.law_id} value={law.law_id}>
                  {law.law_title} ({law.article_count}条)
                </option>
              ))}
            </select>

            <div className="chip-row">
              {CORE_LAWS.slice(0, 5).map((core) => (
                <button
                  key={core.idPrefix}
                  type="button"
                  className={`chip ${selectedLawId?.startsWith(core.idPrefix) ? 'active' : ''}`}
                  onClick={() => handleCoreLawClick(core.idPrefix, core.title)}
                >
                  {core.label}
                </button>
              ))}
            </div>
          </div>

          <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', flexWrap: 'wrap' }}>
            <select
              className="select-box"
              value={layoutKind}
              onChange={(e) => setLayoutKind(e.target.value as LayoutKind)}
            >
              <option value="cose">力学ネットワーク (CoSE)</option>
              <option value="concentric">ハブ中心 (同心円)</option>
              <option value="breadthfirst">階層ツリー</option>
            </select>

            <form onSubmit={handleFocusNodeByQuery} style={{ display: 'flex', gap: '0.35rem' }}>
              <div className="input-box">
                <Search size={14} color="#94a3b8" />
                <input
                  type="text"
                  placeholder="条文へフォーカス (例: 90)"
                  value={nodeSearch}
                  onChange={(e) => setNodeSearch(e.target.value)}
                />
              </div>
            </form>

            <button
              type="button"
              className="btn"
              onClick={() => cyRef.current?.fit(undefined, 30)}
              title="全体表示"
            >
              <Maximize2 size={14} />
              Fit
            </button>
          </div>
        </div>

        {loading ? (
          <div className="empty-state">ネットワークデータを構築中...</div>
        ) : (
          <div ref={containerRef} className="graph-canvas" />
        )}
      </div>

      <aside className="graph-inspector">
        <div>
          <h3 style={{ margin: '0 0 0.5rem', fontSize: '0.95rem' }}>法令グラフ統計</h3>
          <div className="chip-row">
            <span className="chip">条文ノード: {graph.stats.nodeCount}</span>
            <span className="chip active">参照エッジ: {graph.stats.edgeCount}</span>
          </div>
          {graph.stats.topHub && (
            <div style={{ marginTop: '0.6rem', fontSize: '0.82rem', color: '#cbd5e1' }}>
              最多被参照ハブ:{' '}
              <button
                type="button"
                className="chip amber"
                onClick={() => {
                  const hubNum = graph.stats.topHub!.article_num;
                  setFocusedArticleNum(hubNum);
                  const cy = cyRef.current;
                  const node = cy?.getElementById(hubNum);
                  if (cy && node && node.nonempty()) {
                    highlightNode(cy, node as NodeSingular);
                    cy.animate({ center: { eles: node }, zoom: 1.4, duration: 300 });
                  }
                }}
              >
                第{graph.stats.topHub.article_num}条 ({graph.stats.topHub.inDegree}件)
              </button>
            </div>
          )}
        </div>

        <hr style={{ border: 'none', borderTop: '1px solid var(--border-subtle)', width: '100%' }} />

        {focusedArticle ? (
          <div style={{ display: 'flex', flexDirection: 'column', gap: '0.75rem' }}>
            <div>
              <div style={{ fontSize: '0.75rem', color: '#94a3b8' }}>
                {focusedArticle.hierarchy_path}
              </div>
              <h4 style={{ margin: '0.25rem 0', fontSize: '0.98rem' }}>
                {focusedArticle.title}
              </h4>
            </div>

            <button
              type="button"
              className="btn primary"
              onClick={() =>
                selectedLawId && onOpenInViewer(selectedLawId, focusedArticle.article_num)
              }
            >
              <BookOpen size={14} />
              ビューワーで条文を読む
            </button>

            <div>
              <div style={{ fontSize: '0.8rem', color: '#38bdf8', marginBottom: '0.35rem' }}>
                参照先 Outbound ({focusedArticle.outbound_references.length})
              </div>
              <div className="chip-row">
                {focusedArticle.outbound_references.length === 0 ? (
                  <span style={{ fontSize: '0.78rem', color: '#64748b' }}>なし</span>
                ) : (
                  focusedArticle.outbound_references.map((ref) => {
                    const target = parseRefArticleKey(ref);
                    const valid = target && articleNumSet.has(target);
                    return (
                      <button
                        key={ref}
                        type="button"
                        className={`chip ${valid ? 'active' : ''}`}
                        disabled={!valid}
                        onClick={() => {
                          if (!target || !cyRef.current) return;
                          setFocusedArticleNum(target);
                          const node = cyRef.current.getElementById(target);
                          if (node.nonempty()) {
                            highlightNode(cyRef.current, node as NodeSingular);
                          }
                        }}
                      >
                        {ref}
                      </button>
                    );
                  })
                )}
              </div>
            </div>

            <div>
              <div style={{ fontSize: '0.8rem', color: '#fbbf24', marginBottom: '0.35rem' }}>
                被参照元 Inbound ({focusedArticle.inbound_references.length})
              </div>
              <div className="chip-row">
                {focusedArticle.inbound_references.length === 0 ? (
                  <span style={{ fontSize: '0.78rem', color: '#64748b' }}>なし</span>
                ) : (
                  focusedArticle.inbound_references.map((ref) => {
                    const target = parseRefArticleKey(ref);
                    const valid = target && articleNumSet.has(target);
                    return (
                      <button
                        key={ref}
                        type="button"
                        className={`chip ${valid ? 'amber' : ''}`}
                        disabled={!valid}
                        onClick={() => {
                          if (!target || !cyRef.current) return;
                          setFocusedArticleNum(target);
                          const node = cyRef.current.getElementById(target);
                          if (node.nonempty()) {
                            highlightNode(cyRef.current, node as NodeSingular);
                          }
                        }}
                      >
                        {ref}
                      </button>
                    );
                  })
                )}
              </div>
            </div>
          </div>
        ) : (
          <div className="empty-state" style={{ padding: '1rem 0' }}>
            グラフ上のノードをクリックすると、条文リンク・トレーサーが表示されます。
            <br />
            <span style={{ fontSize: '0.76rem', color: '#64748b' }}>
              青 = 参照先 / 琥珀 = 被参照元
            </span>
          </div>
        )}
      </aside>
    </div>
  );
}
