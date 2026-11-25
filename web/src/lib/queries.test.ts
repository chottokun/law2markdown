import { beforeEach, describe, expect, it, vi } from 'vitest';
import type { AnalyticsSummary, LawCatalogEntry } from './types';

const { getDuckDbMock, queryMock } = vi.hoisted(() => {
  const query = vi.fn();
  return {
    queryMock: query,
    getDuckDbMock: vi.fn(async () => ({
      conn: {
        query,
        prepare: vi.fn(),
      },
    })),
  };
});

vi.mock('./duckdb', () => ({
  getDuckDb: getDuckDbMock,
}));

import { fetchAnalyticsSummary, fetchLawCatalog, resetQueryCaches } from './queries';

describe('queries remote summary fast-path and DuckDB fallback', () => {
  beforeEach(() => {
    resetQueryCaches();
    getDuckDbMock.mockClear();
    queryMock.mockReset();
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
});
