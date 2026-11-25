import { describe, expect, it } from 'vitest';
import { buildHierarchyTree } from './hierarchyTree';
import type { ArticleSummary } from './types';

describe('buildHierarchyTree', () => {
  it('groups articles under nested chapter and section hierarchy nodes', () => {
    const articles: ArticleSummary[] = [
      {
        law_id: 'L1',
        article_num: '1',
        hierarchy_path: 'テスト法 > 第一章　総則 > 第一条（目的）',
        title: 'テスト法 第一条',
        outbound_references: [],
        inbound_references: [],
        defined_terms: [],
      },
      {
        law_id: 'L1',
        article_num: '2',
        hierarchy_path: 'テスト法 > 第一章　総則 > 第一節　通則 > 第二条（定義）',
        title: 'テスト法 第二条',
        outbound_references: [],
        inbound_references: [],
        defined_terms: [],
      },
      {
        law_id: 'L1',
        article_num: '3',
        hierarchy_path: 'テスト法 > 第三条',
        title: 'テスト法 第三条',
        outbound_references: [],
        inbound_references: [],
        defined_terms: [],
      },
    ];

    const tree = buildHierarchyTree(articles);
    expect(tree.children.map((c) => c.label)).toEqual(['第一章　総則', '本則']);
    expect(tree.children[0].articles).toHaveLength(1);
    expect(tree.children[0].children[0].label).toBe('第一節　通則');
    expect(tree.children[0].children[0].articles[0].article_num).toBe('2');
    expect(tree.children[1].articles[0].article_num).toBe('3');
  });
});
