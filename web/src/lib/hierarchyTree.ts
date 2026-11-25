import type { ArticleSummary } from './types';

export interface HierarchyNode {
  id: string;
  label: string;
  children: HierarchyNode[];
  articles: ArticleSummary[];
}

/**
 * 条文の `hierarchy_path`（例: `民法 > 第一編　総則 > 第一章　通則 > 第一条`）から
 * 折りたたみ可能な階層ツリーを構築する。
 */
export function buildHierarchyTree(articles: ArticleSummary[]): HierarchyNode {
  const root: HierarchyNode = {
    id: 'root',
    label: '目次',
    children: [],
    articles: [],
  };

  for (const article of articles) {
    const segments = article.hierarchy_path
      .split(' > ')
      .map((s) => s.trim())
      .filter(Boolean);

    // 先頭（法令名）と末尾（条文自身）を除いた中間階層をツリー化する
    const folderSegments = segments.length > 2 ? segments.slice(1, -1) : ['本則'];
    let current = root;
    let pathAcc = '';

    for (const seg of folderSegments) {
      pathAcc = pathAcc ? `${pathAcc} > ${seg}` : seg;
      let child = current.children.find((c) => c.label === seg);
      if (!child) {
        child = {
          id: pathAcc,
          label: seg,
          children: [],
          articles: [],
        };
        current.children.push(child);
      }
      current = child;
    }

    current.articles.push(article);
  }

  return root;
}
