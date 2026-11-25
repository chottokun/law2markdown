import { describe, expect, it } from 'vitest';
import {
  computeArticleDiffList,
  computeLineDiff,
  findMultiVersionLaws,
  parseLawVersionLabel,
} from './diffUtils';
import type { ArticleContentRow, LawCatalogEntry } from './types';

describe('parseLawVersionLabel', () => {
  it('formats e-Gov effective date suffix into a readable label', () => {
    expect(parseLawVersionLabel('325AC0000000226_20250401_507AC0000000001')).toBe(
      '2025-04-01 施行版 (507AC00000)',
    );
    expect(parseLawVersionLabel('321CONSTITUTION')).toBe('321CONSTITUTION');
  });
});

describe('findMultiVersionLaws', () => {
  it('groups laws with 2+ versions and sorts versions chronologically by law_id', () => {
    const catalog: LawCatalogEntry[] = [
      {
        law_id: '325AC0000000226_20260401_002',
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
        law_id: '321CONSTITUTION',
        law_num: '昭和二十一年憲法',
        law_title: '日本国憲法',
        article_count: 103,
      },
    ];

    const groups = findMultiVersionLaws(catalog);
    expect(groups).toHaveLength(1);
    expect(groups[0].lawTitle).toBe('地方税法');
    expect(groups[0].versions.map((v) => v.law_id)).toEqual([
      '325AC0000000226_20250401_001',
      '325AC0000000226_20260401_002',
    ]);
  });
});

describe('computeArticleDiffList', () => {
  it('classifies modified, added, removed, and unchanged articles', () => {
    const oldArts: ArticleContentRow[] = [
      { article_num: '1', hierarchy_path: '法 > 1', title: '第一条', content: '<a id="p1"></a>同一本文' },
      { article_num: '2', hierarchy_path: '法 > 2', title: '第二条', content: '旧テキスト' },
      { article_num: '3', hierarchy_path: '法 > 3', title: '第三条', content: '削除される条文' },
    ];
    const newArts: ArticleContentRow[] = [
      { article_num: '1', hierarchy_path: '法 > 1', title: '第一条', content: '同一本文' },
      { article_num: '2', hierarchy_path: '法 > 2', title: '第二条', content: '新テキスト' },
      { article_num: '4', hierarchy_path: '法 > 4', title: '第四条', content: '新設された条文' },
    ];

    const summary = computeArticleDiffList(oldArts, newArts);
    expect(summary.unchangedCount).toBe(1);
    expect(summary.modifiedCount).toBe(1);
    expect(summary.addedCount).toBe(1);
    expect(summary.removedCount).toBe(1);
    expect(summary.items.map((i) => [i.article_num, i.kind])).toEqual([
      ['2', 'modified'],
      ['3', 'removed'],
      ['4', 'added'],
    ]);
  });
});

describe('computeLineDiff', () => {
  it('computes line-level added, removed, and context lines', () => {
    const diff = computeLineDiff('行1\n旧行2\n行3', '行1\n新行2\n行3\n行4');
    expect(diff).toEqual([
      { type: 'context', text: '行1' },
      { type: 'removed', text: '旧行2' },
      { type: 'added', text: '新行2' },
      { type: 'context', text: '行3' },
      { type: 'added', text: '行4' },
    ]);
  });
});
