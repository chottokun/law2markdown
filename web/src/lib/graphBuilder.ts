import type { ArticleSummary } from './types';

export interface GraphNodeElement {
  data: {
    id: string;
    label: string;
    title: string;
    hierarchy_path: string;
    inDegree: number;
    outDegree: number;
    size: number;
    definedTermCount: number;
  };
}

export interface GraphEdgeElement {
  data: {
    id: string;
    source: string;
    target: string;
  };
}

export interface LawGraphResult {
  nodes: GraphNodeElement[];
  edges: GraphEdgeElement[];
  stats: {
    nodeCount: number;
    edgeCount: number;
    topHub: { article_num: string; title: string; inDegree: number } | null;
  };
}

/**
 * 参照キー（例: `art_003_第三条`, `art_4_2_第四条の二`, `../articles/art_012_第十二条.md`）
 * から正規化された `article_num`（例: `3`, `4_2`, `12`）を抽出する。
 */
export function parseRefArticleKey(ref: string): string | null {
  if (!ref) return null;
  const basename = ref.split('/').pop() ?? ref;
  const match = basename.match(/^art_([0-9]+(?:_[0-9]+)*)(?:_|\.|$)/);
  if (!match) return null;

  return match[1]
    .split('_')
    .map((part) => String(Number.parseInt(part, 10)))
    .join('_');
}

/**
 * 法令番号文字列（例: `昭和二十二年法律第四十九号`）から元号を抽出する。
 */
export function extractEraFromLawNum(lawNum: string): string {
  const eras = ['令和', '平成', '昭和', '大正', '明治'] as const;
  for (const era of eras) {
    if (lawNum.startsWith(era)) return era;
  }
  return 'その他';
}

function formatShortArticleLabel(articleNum: string): string {
  const parts = articleNum.split('_');
  if (parts.length === 1) return `第${parts[0]}条`;
  return `第${parts[0]}条の${parts.slice(1).join('の')}`;
}

/**
 * 法令内の条文サマリ一覧から Cytoscape.js 用のグラフノード・エッジ要素を構築する。
 */
export function buildLawGraphElements(articles: ArticleSummary[]): LawGraphResult {
  const uniqueArticles: ArticleSummary[] = [];
  const seenIds = new Set<string>();
  for (const art of articles) {
    const id = art.article_num.trim();
    if (!id || seenIds.has(id)) continue;
    seenIds.add(id);
    uniqueArticles.push(id === art.article_num ? art : { ...art, article_num: id });
  }

  const knownIds = seenIds;
  const edgeSet = new Set<string>();
  const edges: GraphEdgeElement[] = [];
  const inCount = new Map<string, number>();
  const outCount = new Map<string, number>();

  for (const art of uniqueArticles) {
    inCount.set(art.article_num, 0);
    outCount.set(art.article_num, 0);
  }

  for (const art of uniqueArticles) {
    for (const ref of art.outbound_references) {
      const targetNum = parseRefArticleKey(ref);
      if (!targetNum || targetNum === art.article_num || !knownIds.has(targetNum)) {
        continue;
      }
      const edgeKey = `${art.article_num}->${targetNum}`;
      if (edgeSet.has(edgeKey)) continue;
      edgeSet.add(edgeKey);
      edges.push({
        data: {
          id: edgeKey,
          source: art.article_num,
          target: targetNum,
        },
      });
      outCount.set(art.article_num, (outCount.get(art.article_num) ?? 0) + 1);
      inCount.set(targetNum, (inCount.get(targetNum) ?? 0) + 1);
    }
  }

  let topHub: { article_num: string; title: string; inDegree: number } | null = null;
  const nodes: GraphNodeElement[] = [];
  for (const art of uniqueArticles) {
    const inDeg = Math.max(inCount.get(art.article_num) ?? 0, art.inbound_references.length);
    const outDeg = outCount.get(art.article_num) ?? 0;
    const size = Math.min(58, 22 + Math.round(Math.sqrt(inDeg) * 7));

    if (!topHub || inDeg > topHub.inDegree) {
      topHub = { article_num: art.article_num, title: art.title, inDegree: inDeg };
    }

    nodes.push({
      data: {
        id: art.article_num,
        label: formatShortArticleLabel(art.article_num),
        title: art.title,
        hierarchy_path: art.hierarchy_path,
        inDegree: inDeg,
        outDegree: outDeg,
        size,
        definedTermCount: art.defined_terms.length,
      },
    });
  }

  if (topHub && topHub.inDegree === 0) {
    topHub = null;
  }

  return {
    nodes,
    edges,
    stats: {
      nodeCount: nodes.length,
      edgeCount: edges.length,
      topHub,
    },
  };
}
