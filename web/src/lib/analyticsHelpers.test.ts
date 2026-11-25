import { describe, expect, it } from 'vitest';
import {
  deduplicateLawCatalog,
  deduplicateLawRanking,
  getBaseLawKey,
} from './analyticsHelpers';
import type { LawCatalogEntry } from './types';

describe('getBaseLawKey', () => {
  it('extracts base e-Gov law ID prefix before the effective-date suffix', () => {
    expect(getBaseLawKey('325AC0000000226_20250401_507AC0000000001', '昭和二十五年法律第二百二十六号', '地方税法')).toBe(
      '325AC0000000226',
    );
    expect(getBaseLawKey('321CONSTITUTION', '昭和二十一年憲法', '日本国憲法')).toBe(
      '321CONSTITUTION',
    );
  });
});

describe('deduplicateLawCatalog', () => {
  it('keeps one representative version per law and sorts by article_count descending', () => {
    const catalog: LawCatalogEntry[] = [
      {
        law_id: '325AC0000000226_20260401_999',
        law_num: '昭和二十五年法律第二百二十六号',
        law_title: '地方税法',
        article_count: 1380,
      },
      {
        law_id: '325AC0000000226_20250401_001',
        law_num: '昭和二十五年法律第二百二十六号',
        law_title: '地方税法',
        article_count: 1375,
      },
      {
        law_id: '129AC0000000089_20250401_001',
        law_num: '明治二十九年法律第八十九号',
        law_title: '民法',
        article_count: 1050,
      },
    ];

    const deduped = deduplicateLawCatalog(catalog);
    expect(deduped).toHaveLength(2);
    expect(deduped[0].law_title).toBe('地方税法');
    expect(deduped[0].law_id).toBe('325AC0000000226_20250401_001');
    expect(deduped[1].law_title).toBe('民法');
  });
});

describe('deduplicateLawRanking', () => {
  it('removes duplicate versions of the same law in ranking results', () => {
    const rows = [
      { law_id: 'A_2026', law_title: '金融商品取引法', count: 240 },
      { law_id: 'A_2025', law_title: '金融商品取引法', count: 235 },
      { law_id: 'B_2025', law_title: '電波法施行規則', count: 170 },
      { law_id: 'C_2025', law_title: '会社法', count: 150 },
    ];

    const top = deduplicateLawRanking(rows, 2);
    expect(top.map((r) => r.law_title)).toEqual(['金融商品取引法', '電波法施行規則']);
  });
});
