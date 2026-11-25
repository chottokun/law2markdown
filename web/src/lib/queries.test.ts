import { beforeEach, describe, expect, it, vi } from 'vitest';
import type { AnalyticsSummary, LawCatalogEntry } from './types';

const { getDuckDbMock, prepareMock, queryMock } = vi.hoisted(() => {
  const query = vi.fn();
  const prepare = vi.fn();
  return {
    queryMock: query,
    prepareMock: prepare,
    getDuckDbMock: vi.fn(async () => ({
      conn: {
        query,
        prepare,
      },
    })),
  };
});

vi.mock('./duckdb', () => ({
  getDuckDb: getDuckDbMock,
}));

import {
  fetchAnalyticsSummary,
  fetchLawCatalog,
  resetQueryCaches,
  searchDefinedTerms,
} from './queries';

describe('queries remote summary fast-path and DuckDB fallback', () => {
  beforeEach(() => {
    resetQueryCaches();
    getDuckDbMock.mockClear();
    queryMock.mockReset();
    prepareMock.mockReset();
    vi.restoreAllMocks();
  });

  it('uses laws_summary.json without initializing DuckDB when available', async () => {
    const mockCatalog: LawCatalogEntry[] = [
      {
        law_id: '321CONSTITUTION',
        law_num: '昭和二十一年憲法',
        law_title: '日本国憲法',
        article_count: 103,
      },
    ];
    const mockAnalytics: AnalyticsSummary = {
      totalArticles: 103,
      totalLaws: 1,
      totalLawVersions: 1,
      totalOutboundEdges: 10,
      totalDefinedTerms: 0,
      eraDistribution: [{ era: '昭和', count: 1 }],
      topLawsByArticles: [
        {
          law_id: '321CONSTITUTION',
          law_title: '日本国憲法',
          law_num: '昭和二十一年憲法',
          count: 103,
        },
      ],
      topLawsByTerms: [],
    };

    vi.stubGlobal(
      'fetch',
      vi.fn(async () => ({
        ok: true,
        json: async () => ({ catalog: mockCatalog, analytics: mockAnalytics }),
      })),
    );

    const catalog = await fetchLawCatalog();
    const analytics = await fetchAnalyticsSummary();

    expect(catalog).toEqual(mockCatalog);
    expect(analytics).toEqual(mockAnalytics);
    expect(getDuckDbMock).not.toHaveBeenCalled();
  });

  it('falls back to DuckDB-Wasm when laws_summary.json returns 404', async () => {
    vi.stubGlobal(
      'fetch',
      vi.fn(async () => ({
        ok: false,
        status: 404,
      })),
    );

    queryMock.mockResolvedValueOnce({
      toArray: () => [
        {
          law_id: '321CONSTITUTION',
          law_num: '昭和二十一年憲法',
          law_title: '日本国憲法',
          article_count: 103,
        },
      ],
    });

    const catalog = await fetchLawCatalog();
    expect(catalog).toHaveLength(1);
    expect(catalog[0].law_title).toBe('日本国憲法');
    expect(getDuckDbMock).toHaveBeenCalledTimes(1);
  });

  it('searches defined terms without lambda parameters and deduplicates law versions', async () => {
    const stmtQuery = vi.fn(async () => ({
      toArray: () => [
        {
          law_id: '322AC0000000049_20250401_001',
          law_num: '昭和二十二年法律第四十九号',
          law_title: '労働基準法',
          article_num: '9',
          hierarchy_path: '労働基準法 > 第九条',
          title: '労働基準法 第九条',
          defined_terms: ['労働者', '賃金'],
          snippet: '<a id="p1"></a>この法律で労働者とは...',
        },
        {
          law_id: '322AC0000000049_20260401_002',
          law_num: '昭和二十二年法律第四十九号',
          law_title: '労働基準法',
          article_num: '9',
          hierarchy_path: '労働基準法 > 第九条',
          title: '労働基準法 第九条',
          defined_terms: ['労働者'],
          snippet: '重複バージョン',
        },
      ],
    }));
    const stmtClose = vi.fn(async () => undefined);
    prepareMock.mockResolvedValueOnce({ query: stmtQuery, close: stmtClose });

    const hits = await searchDefinedTerms('労働者', 20);
    expect(prepareMock).toHaveBeenCalledTimes(1);
    expect(prepareMock.mock.calls[0][0]).not.toContain('list_filter');
    expect(stmtQuery).toHaveBeenCalledWith('%労働者%', 60);
    expect(stmtClose).toHaveBeenCalledTimes(1);
    expect(hits).toHaveLength(1);
    expect(hits[0].matched_terms).toEqual(['労働者']);
    expect(hits[0].snippet).toBe('この法律で労働者とは...');
  });
});
