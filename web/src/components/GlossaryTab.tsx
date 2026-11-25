import { BookMarked, BookOpen, Search } from 'lucide-react';
import { useEffect, useState } from 'react';
import { fetchTopDefinedTerms, searchDefinedTerms } from '../lib/queries';
import type { PopularTermEntry, TermDefinitionHit } from '../lib/types';

interface GlossaryTabProps {
  onOpenInViewer: (lawId: string, articleNum: string) => void;
  onNotify: (kind: 'info' | 'success' | 'error', text: string) => void;
}

const FALLBACK_POPULAR_TERMS = [
  '労働者',
  '事業者',
  '個人情報',
  '電磁的記録',
  '中小企業者',
  '指定',
  '届出',
  '記録',
];

export function GlossaryTab({ onOpenInViewer, onNotify }: GlossaryTabProps) {
  const [popularTerms, setPopularTerms] = useState<PopularTermEntry[]>([]);
  const [queryText, setQueryText] = useState('労働者');
  const [activeQuery, setActiveQuery] = useState('');
  const [results, setResults] = useState<TermDefinitionHit[]>([]);
  const [loading, setLoading] = useState(false);

  const runSearch = async (term: string) => {
    const trimmed = term.trim();
    if (!trimmed) return;
    setLoading(true);
    setActiveQuery(trimmed);
    try {
      const hits = await searchDefinedTerms(trimmed, 60);
      setResults(hits);
      if (hits.length === 0) {
        onNotify('info', `「${trimmed}」の定義規定は見つかりませんでした。`);
      }
    } catch (err) {
      onNotify('error', err instanceof Error ? err.message : '用語検索に失敗しました');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    let cancelled = false;
    fetchTopDefinedTerms(24)
      .then((list) => {
        if (!cancelled) setPopularTerms(list);
      })
      .catch(() => {
        // 人気用語取得失敗時はフォールバックチップを維持
      });

    void runSearch('労働者');
    return () => {
      cancelled = true;
    };
  }, []);

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    void runSearch(queryText);
  };

  const handleChipClick = (term: string) => {
    setQueryText(term);
    void runSearch(term);
  };

  return (
    <div className="analytics-scroll">
      <div className="analytics-container">
        <section className="panel-card">
          <h3>
            <span style={{ display: 'inline-flex', alignItems: 'center', gap: '0.45rem' }}>
              <BookMarked size={16} color="#38bdf8" />
              横断・法定用語辞典（法令ごとの定義比較）
            </span>
          </h3>

          <form
            onSubmit={handleSubmit}
            style={{ display: 'flex', gap: '0.5rem', marginBottom: '0.85rem', flexWrap: 'wrap' }}
          >
            <div className="input-box" style={{ flex: '1 1 280px' }}>
              <Search size={15} color="#94a3b8" />
              <input
                type="text"
                placeholder="定義用語を検索（例: 労働者, 個人情報, 電磁的記録）"
                value={queryText}
                onChange={(e) => setQueryText(e.target.value)}
              />
            </div>
            <button type="submit" className="btn primary" disabled={loading}>
              {loading ? '検索中...' : '定義を横断検索'}
            </button>
          </form>

          <div style={{ fontSize: '0.78rem', color: '#94a3b8', marginBottom: '0.4rem' }}>
            多くの法律で定義されている主要用語:
          </div>
          <div className="chip-row">
            {popularTerms.length > 0
              ? popularTerms.map((item) => (
                  <button
                    key={item.term}
                    type="button"
                    className={`chip ${activeQuery === item.term ? 'active' : ''}`}
                    onClick={() => handleChipClick(item.term)}
                  >
                    {item.term} ({item.law_count}法令)
                  </button>
                ))
              : FALLBACK_POPULAR_TERMS.map((term) => (
                  <button
                    key={term}
                    type="button"
                    className={`chip ${activeQuery === term ? 'active' : ''}`}
                    onClick={() => handleChipClick(term)}
                  >
                    {term}
                  </button>
                ))}
          </div>
        </section>

        <section>
          <div
            style={{
              display: 'flex',
              justifyContent: 'space-between',
              alignItems: 'center',
              marginBottom: '0.75rem',
            }}
          >
            <span style={{ fontSize: '0.88rem', color: '#cbd5e1' }}>
              {activeQuery
                ? `「${activeQuery}」を含む定義規定: ${results.length} 法令・条文`
                : '検索してください'}
            </span>
          </div>

          {loading ? (
            <div className="panel-card">
              <div className="empty-state">全法令の定義レジストリを横断検索中...</div>
            </div>
          ) : results.length === 0 ? (
            <div className="panel-card">
              <div className="empty-state">該当する定義規定はありません</div>
            </div>
          ) : (
            <div className="glossary-grid">
              {results.map((hit) => (
                <article
                  key={`${hit.law_id}-${hit.article_num}`}
                  className="glossary-card"
                >
                  <div className="glossary-card-head">
                    <div>
                      <h4 className="glossary-law-title">{hit.law_title}</h4>
                      <div className="glossary-law-meta">
                        {hit.law_num} ・ 第{hit.article_num}条
                      </div>
                    </div>
                    <button
                      type="button"
                      className="btn"
                      onClick={() => onOpenInViewer(hit.law_id, hit.article_num)}
                    >
                      <BookOpen size={13} />
                      条文を開く
                    </button>
                  </div>

                  <div className="chip-row">
                    {hit.matched_terms.map((t) => (
                      <span key={t} className="chip emerald">
                        {t}
                      </span>
                    ))}
                  </div>

                  <p className="glossary-snippet">{hit.snippet}...</p>
                </article>
              ))}
            </div>
          )}
        </section>
      </div>
    </div>
  );
}
