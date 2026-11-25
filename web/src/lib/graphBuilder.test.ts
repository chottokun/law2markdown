import { describe, expect, it } from 'vitest';
import {
  buildLawGraphElements,
  extractEraFromLawNum,
  parseRefArticleKey,
} from './graphBuilder';
import type { ArticleSummary } from './types';

describe('parseRefArticleKey', () => {
  it('extracts article_num from standard and branch article reference filenames', () => {
    expect(parseRefArticleKey('art_003_第三条')).toBe('3');
    expect(parseRefArticleKey('art_090_第九十条')).toBe('90');
    expect(parseRefArticleKey('art_4_2_第四条の二')).toBe('4_2');
    expect(parseRefArticleKey('art_001_2_第一条の二')).toBe('1_2');
    expect(parseRefArticleKey('../articles/art_012_第十二条.md')).toBe('12');
    expect(parseRefArticleKey('table_001_別表第一')).toBeNull();
    expect(parseRefArticleKey('')).toBeNull();
  });
});

describe('extractEraFromLawNum', () => {
  it('identifies Japanese eras and falls back to その他', () => {
    expect(extractEraFromLawNum('明治二十九年法律第八十九号')).toBe('明治');
    expect(extractEraFromLawNum('大正十一年法律第七十一号')).toBe('大正');
    expect(extractEraFromLawNum('昭和二十二年法律第四十九号')).toBe('昭和');
    expect(extractEraFromLawNum('平成十五年法律第五十七号')).toBe('平成');
    expect(extractEraFromLawNum('令和五年法律第二十五号')).toBe('令和');
    expect(extractEraFromLawNum('不明な法令番号')).toBe('その他');
  });
});

describe('buildLawGraphElements', () => {
  it('builds deduplicated directed edges and computes degree weights', () => {
    const articles: ArticleSummary[] = [
      {
        law_id: 'LAW1',
        article_num: '1',
        hierarchy_path: 'テスト法 > 第一条',
        title: 'テスト法 第一条',
        outbound_references: ['art_002_第二条', 'art_002_第二条', 'art_999_存在しない条'],
        inbound_references: [],
        defined_terms: ['労働者'],
      },
      {
        law_id: 'LAW1',
        article_num: '2',
        hierarchy_path: 'テスト法 > 第二条',
        title: 'テスト法 第二条',
        outbound_references: ['art_001_第一条'],
        inbound_references: ['art_001_第一条', 'art_003_第三条'],
        defined_terms: [],
      },
      {
        law_id: 'LAW1',
        article_num: '3',
        hierarchy_path: 'テスト法 > 第三条',
        title: 'テスト法 第三条',
        outbound_references: ['art_002_第二条'],
        inbound_references: [],
        defined_terms: [],
      },
    ];

    const result = buildLawGraphElements(articles);
    expect(result.nodes).toHaveLength(3);
    expect(result.edges).toHaveLength(3);
    expect(result.stats.nodeCount).toBe(3);
    expect(result.stats.edgeCount).toBe(3);
    expect(result.stats.topHub?.article_num).toBe('2');

    const node2 = result.nodes.find((n) => n.data.id === '2');
    expect(node2?.data.inDegree).toBe(2);
    expect(node2?.data.size).toBeGreaterThan(22);
  });
});
