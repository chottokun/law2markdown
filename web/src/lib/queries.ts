import { deduplicateLawCatalog, deduplicateLawRanking } from './analyticsHelpers';
import { getBaseLawKey } from './analyticsHelpers';
import { SUMMARY_JSON_URL } from './constants';
import { getDuckDb } from './duckdb';
import { extractEraFromLawNum } from './graphBuilder';
import { stripHtmlTags } from './sanitize';
import { validateReadOnlySql } from './sqlSafety';
import type {
  AnalyticsSummary,
  ArticleContentRow,
  ArticleDetail,
  ArticleSummary,
  LawCatalogEntry,
  PopularTermEntry,
  SearchResultEntry,
  SqlQueryResult,
  TermDefinitionHit,
} from './types';

let catalogCache: LawCatalogEntry[] | null = null;
let analyticsCache: AnalyticsSummary | null = null;
let topTermsCache: PopularTermEntry[] | null = null;
let summaryFetchPromise: Promise<boolean> | null = null;

export function resetQueryCaches(): void {
  catalogCache = null;
  analyticsCache = null;
  topTermsCache = null;
  summaryFetchPromise = null;
}

async function tryLoadRemoteSummary(): Promise<boolean> {
  if (catalogCache && analyticsCache) {
    return true;
  }
  if (summaryFetchPromise) {
    return summaryFetchPromise;
  }

  summaryFetchPromise = (async () => {
    if (typeof fetch !== 'function') return false;
    const controller = new AbortController();
    const timer = setTimeout(() => controller.abort(), 4000);
    try {
      const res = await fetch(SUMMARY_JSON_URL, { signal: controller.signal });
      if (!res.ok) return false;
      const payload = (await res.json()) as {
        catalog?: LawCatalogEntry[];
        analytics?: AnalyticsSummary;
      };
      if (
        !Array.isArray(payload?.catalog) ||
        !payload?.analytics ||
        typeof payload.analytics.totalArticles !== 'number'
      ) {
        return false;
      }
      catalogCache = payload.catalog;
      analyticsCache = payload.analytics;
      return true;
    } catch {
      return false;
    } finally {
      clearTimeout(timer);
    }
  })();

  return summaryFetchPromise;
}

function toNumber(val: unknown): number {
  if (typeof val === 'number') return val;
  if (typeof val === 'bigint') return Number(val);
  return Number(val ?? 0) || 0;
}

function toStringArray(val: unknown): string[] {
  if (!val) return [];
  if (Array.isArray(val)) return val.map((v) => String(v));
  if (
    typeof val === 'object' &&
    'toArray' in val &&
    typeof (val as { toArray: unknown }).toArray === 'function'
  ) {
    return Array.from((val as { toArray: () => unknown[] }).toArray(), (v) => String(v));
  }
  if (typeof Symbol !== 'undefined' && Symbol.iterator in Object(val)) {
    return Array.from(val as Iterable<unknown>, (v) => String(v));
  }
  return [];
}

function normalizeCellValue(val: unknown): unknown {
  if (val === null || val === undefined) return null;
  if (typeof val === 'bigint') {
    return val <= BigInt(Number.MAX_SAFE_INTEGER) && val >= BigInt(Number.MIN_SAFE_INTEGER)
      ? Number(val)
      : val.toString();
  }
  if (
    typeof val === 'object' &&
    'toArray' in val &&
    typeof (val as { toArray: unknown }).toArray === 'function'
  ) {
    return Array.from((val as { toArray: () => unknown[] }).toArray(), normalizeCellValue);
  }
  return val;
}

function escapeLikePattern(term: string): string {
  return term.replace(/[\\%_]/g, (ch) => `\\${ch}`);
}

/**
 * 全法令一覧（メタデータ＋条文数）を取得する。content カラムは読み込まない。
 */
export async function fetchLawCatalog(): Promise<LawCatalogEntry[]> {
  if (catalogCache) {
    return catalogCache;
  }
  if (await tryLoadRemoteSummary() && catalogCache) {
    return catalogCache;
  }

  const { conn } = await getDuckDb();
  const table = await conn.query(`
    SELECT
      law_id,
      MIN(law_num) AS law_num,
      MIN(law_title) AS law_title,
      COUNT(*) AS article_count
    FROM laws_articles
    GROUP BY law_id
    ORDER BY article_count DESC, law_title ASC
  `);

  const rows = table.toArray() as Record<string, unknown>[];
  catalogCache = rows.map((row) => ({
    law_id: String(row.law_id ?? ''),
    law_num: String(row.law_num ?? ''),
    law_title: String(row.law_title ?? ''),
    article_count: toNumber(row.article_count),
  }));
  return catalogCache;
}

/**
 * 指定法令の条文一覧（本文以外のメタデータ・参照関係・定義用語）を取得する。
 */
export async function fetchLawArticles(lawId: string): Promise<ArticleSummary[]> {
  const { conn } = await getDuckDb();
  const stmt = await conn.prepare(`
    SELECT
      law_id,
      article_num,
      hierarchy_path,
      title,
      outbound_references,
      inbound_references,
      defined_terms
    FROM laws_articles
    WHERE law_id = ?
      AND article_num IS NOT NULL
      AND TRIM(article_num) <> ''
  `);

  try {
    const table = await stmt.query(lawId);
    const rows = table.toArray() as Record<string, unknown>[];
    const items: ArticleSummary[] = rows.map((row) => ({
      law_id: String(row.law_id ?? ''),
      article_num: String(row.article_num ?? ''),
      hierarchy_path: String(row.hierarchy_path ?? ''),
      title: String(row.title ?? ''),
      outbound_references: toStringArray(row.outbound_references),
      inbound_references: toStringArray(row.inbound_references),
      defined_terms: toStringArray(row.defined_terms),
    }));

    items.sort((a, b) => compareArticleNums(a.article_num, b.article_num));
    return items;
  } finally {
    await stmt.close();
  }
}

function compareArticleNums(a: string, b: string): number {
  const partsA = a.split('_').map((p) => Number.parseInt(p, 10));
  const partsB = b.split('_').map((p) => Number.parseInt(p, 10));
  const len = Math.max(partsA.length, partsB.length);
  for (let i = 0; i < len; i++) {
    const va = partsA[i] ?? 0;
    const vb = partsB[i] ?? 0;
    if (Number.isNaN(va) || Number.isNaN(vb)) {
      return a.localeCompare(b, 'ja');
    }
    if (va !== vb) return va - vb;
  }
  return 0;
}

/**
 * 単一条文の本文（content）を含む詳細を取得する。
 */
export async function fetchArticleDetail(
  lawId: string,
  articleNum: string,
): Promise<ArticleDetail | null> {
  const { conn } = await getDuckDb();
  const stmt = await conn.prepare(`
    SELECT
      law_id,
      law_num,
      law_title,
      article_num,
      hierarchy_path,
      title,
      content,
      outbound_references,
      inbound_references,
      defined_terms,
      child_anchors_json
    FROM laws_articles
    WHERE law_id = ? AND article_num = ?
    LIMIT 1
  `);

  try {
    const table = await stmt.query(lawId, articleNum);
    const rows = table.toArray() as Record<string, unknown>[];
    if (rows.length === 0) return null;
    const row = rows[0];
    return {
      law_id: String(row.law_id ?? ''),
      law_num: String(row.law_num ?? ''),
      law_title: String(row.law_title ?? ''),
      article_num: String(row.article_num ?? ''),
      hierarchy_path: String(row.hierarchy_path ?? ''),
      title: String(row.title ?? ''),
      content: String(row.content ?? ''),
      outbound_references: toStringArray(row.outbound_references),
      inbound_references: toStringArray(row.inbound_references),
      defined_terms: toStringArray(row.defined_terms),
      child_anchors_json: String(row.child_anchors_json ?? '[]'),
    };
  } finally {
    await stmt.close();
  }
}

/**
 * 全法令を横断して条文タイトル・本文のキーワード検索を実行する。
 */
export async function searchArticles(
  keyword: string,
  limit = 50,
): Promise<SearchResultEntry[]> {
  const trimmed = keyword.trim();
  if (!trimmed) return [];

  const safeLimit = Math.max(1, Math.min(100, Math.floor(limit)));
  const pattern = `%${escapeLikePattern(trimmed)}%`;

  const { conn } = await getDuckDb();
  const stmt = await conn.prepare(`
    SELECT
      law_id,
      law_num,
      law_title,
      article_num,
      hierarchy_path,
      title,
      SUBSTR(content, 1, 260) AS snippet
    FROM laws_articles
    WHERE title ILIKE ? ESCAPE '\\' OR content ILIKE ? ESCAPE '\\'
    LIMIT CAST(? AS INTEGER)
  `);

  try {
    const table = await stmt.query(pattern, pattern, safeLimit);
    const rows = table.toArray() as Record<string, unknown>[];
    return rows.map((row) => ({
      law_id: String(row.law_id ?? ''),
      law_num: String(row.law_num ?? ''),
      law_title: String(row.law_title ?? ''),
      article_num: String(row.article_num ?? ''),
      hierarchy_path: String(row.hierarchy_path ?? ''),
      title: String(row.title ?? ''),
      snippet: stripHtmlTags(String(row.snippet ?? '')).replace(/\s+/g, ' ').slice(0, 180),
    }));
  } finally {
    await stmt.close();
  }
}

/**
 * アナリティクス画面用の全体サマリ・分布・ランキングを集計する（content カラム不使用）。
 */
export async function fetchAnalyticsSummary(): Promise<AnalyticsSummary> {
  if (analyticsCache) {
    return analyticsCache;
  }
  if (await tryLoadRemoteSummary() && analyticsCache) {
    return analyticsCache;
  }

  const catalog = await fetchLawCatalog();
  const uniqueCatalog = deduplicateLawCatalog(catalog);
  const totalLawVersions = catalog.length;
  const totalLaws = uniqueCatalog.length;
  const totalArticles = catalog.reduce((acc, item) => acc + item.article_count, 0);

  const eraOrder = ['明治', '大正', '昭和', '平成', '令和', 'その他'];
  const eraMap = new Map<string, number>(eraOrder.map((e) => [e, 0]));
  for (const law of uniqueCatalog) {
    const era = extractEraFromLawNum(law.law_num);
    eraMap.set(era, (eraMap.get(era) ?? 0) + 1);
  }
  const eraDistribution = eraOrder.map((era) => ({ era, count: eraMap.get(era) ?? 0 }));

  const topLawsByArticles = uniqueCatalog.slice(0, 15).map((item) => ({
    law_id: item.law_id,
    law_title: item.law_title,
    law_num: item.law_num,
    count: item.article_count,
  }));

  const { conn } = await getDuckDb();
  const totalsTable = await conn.query(`
    SELECT
      COALESCE(SUM(LEN(outbound_references)), 0) AS total_edges,
      COALESCE(SUM(LEN(defined_terms)), 0) AS total_terms
    FROM laws_articles
  `);
  const totalsRow = (totalsTable.toArray()[0] ?? {}) as Record<string, unknown>;

  const topTermsTable = await conn.query(`
    SELECT law_id, law_title, term_count
    FROM (
      SELECT
        law_id,
        MIN(law_title) AS law_title,
        SUM(LEN(defined_terms)) AS term_count,
        ROW_NUMBER() OVER (
          PARTITION BY split_part(law_id, '_', 1)
          ORDER BY SUM(LEN(defined_terms)) DESC, law_id ASC
        ) AS rn
      FROM laws_articles
      GROUP BY law_id
      HAVING SUM(LEN(defined_terms)) > 0
    )
    WHERE rn = 1
    ORDER BY term_count DESC
    LIMIT 30
  `);
  const topLawsByTerms = deduplicateLawRanking(
    (topTermsTable.toArray() as Record<string, unknown>[]).map((row) => ({
      law_id: String(row.law_id ?? ''),
      law_title: String(row.law_title ?? ''),
      count: toNumber(row.term_count),
    })),
    10,
  );

  analyticsCache = {
    totalArticles,
    totalLaws,
    totalLawVersions,
    totalOutboundEdges: toNumber(totalsRow.total_edges),
    totalDefinedTerms: toNumber(totalsRow.total_terms),
    eraDistribution,
    topLawsByArticles,
    topLawsByTerms,
  };
  return analyticsCache;
}

/**
 * SQL Sandbox 用に読み取り専用クエリを検証・実行し、最大 500 行まで結果を返す。
 */
export async function runSandboxSql(rawSql: string): Promise<SqlQueryResult> {
  const check = validateReadOnlySql(rawSql);
  if (!check.ok) {
    throw new Error(check.error ?? '許可されていない SQL クエリです。');
  }

  const cleanSql = rawSql.trim().replace(/;+\s*$/, '');
  const { conn } = await getDuckDb();

  const started = performance.now();
  const table = await conn.query(cleanSql);
  const elapsedMs = Math.round(performance.now() - started);

  const columns = table.schema.fields.map((f) => f.name);
  const allRows = table.toArray() as Record<string, unknown>[];
  const MAX_ROWS = 500;
  const truncated = allRows.length > MAX_ROWS;

  const rows = allRows.slice(0, MAX_ROWS).map((row) => {
    const out: Record<string, unknown> = {};
    for (const col of columns) {
      out[col] = normalizeCellValue(row[col]);
    }
    return out;
  });

  return {
    columns,
    rows,
    elapsedMs,
    truncated,
  };
}

/**
 * 指定法令の全条文と本文を取得する（新旧 Diff 比較用）。
 */
export async function fetchLawArticlesWithContent(lawId: string): Promise<ArticleContentRow[]> {
  const { conn } = await getDuckDb();
  const stmt = await conn.prepare(`
    SELECT
      article_num,
      hierarchy_path,
      title,
      content
    FROM laws_articles
    WHERE law_id = ?
      AND article_num IS NOT NULL
      AND TRIM(article_num) <> ''
  `);

  try {
    const table = await stmt.query(lawId);
    const rows = table.toArray() as Record<string, unknown>[];
    const items: ArticleContentRow[] = rows.map((row) => ({
      article_num: String(row.article_num ?? ''),
      hierarchy_path: String(row.hierarchy_path ?? ''),
      title: String(row.title ?? ''),
      content: String(row.content ?? ''),
    }));
    items.sort((a, b) => compareArticleNums(a.article_num, b.article_num));
    return items;
  } finally {
    await stmt.close();
  }
}

/**
 * 多くの法令で共通して定義されている法定用語ランキングを取得する。
 */
export async function fetchTopDefinedTerms(limit = 30): Promise<PopularTermEntry[]> {
  if (topTermsCache) {
    return topTermsCache.slice(0, limit);
  }

  const safeLimit = Math.max(1, Math.min(100, Math.floor(limit)));
  const { conn } = await getDuckDb();
  const stmt = await conn.prepare(`
    SELECT
      term,
      COUNT(DISTINCT split_part(law_id, '_', 1)) AS law_count,
      COUNT(*) AS occurrence_count
    FROM (
      SELECT law_id, UNNEST(defined_terms) AS term
      FROM laws_articles
      WHERE LEN(defined_terms) > 0
    )
    WHERE TRIM(term) <> ''
    GROUP BY term
    ORDER BY law_count DESC, occurrence_count DESC
    LIMIT CAST(? AS INTEGER)
  `);

  try {
    const table = await stmt.query(safeLimit);
    const rows = table.toArray() as Record<string, unknown>[];
    topTermsCache = rows.map((row) => ({
      term: String(row.term ?? ''),
      law_count: toNumber(row.law_count),
      occurrence_count: toNumber(row.occurrence_count),
    }));
    return topTermsCache;
  } finally {
    await stmt.close();
  }
}

/**
 * 指定用語（部分一致）を定義している条文を全法令から横断検索し、改正版重複を除外して返す。
 */
export async function searchDefinedTerms(
  termQuery: string,
  limit = 60,
): Promise<TermDefinitionHit[]> {
  const trimmed = termQuery.trim();
  if (!trimmed) return [];

  const safeLimit = Math.max(1, Math.min(100, Math.floor(limit)));
  const fetchLimit = safeLimit * 3;
  const pattern = `%${escapeLikePattern(trimmed)}%`;
  const lowerQuery = trimmed.toLowerCase();

  const { conn } = await getDuckDb();
  const stmt = await conn.prepare(`
    SELECT
      law_id,
      law_num,
      law_title,
      article_num,
      hierarchy_path,
      title,
      defined_terms,
      SUBSTR(content, 1, 500) AS snippet
    FROM laws_articles
    WHERE LEN(defined_terms) > 0
      AND array_to_string(defined_terms, ' || ') ILIKE ? ESCAPE '\\'
      AND article_num IS NOT NULL
      AND TRIM(article_num) <> ''
    LIMIT CAST(? AS INTEGER)
  `);

  try {
    const table = await stmt.query(pattern, fetchLimit);
    const rows = table.toArray() as Record<string, unknown>[];
    const seen = new Set<string>();
    const results: TermDefinitionHit[] = [];

    for (const row of rows) {
      const terms = toStringArray(row.defined_terms);
      const matchedTerms = terms.filter((t) => t.toLowerCase().includes(lowerQuery));
      if (matchedTerms.length === 0) continue;

      const lawId = String(row.law_id ?? '');
      const lawNum = String(row.law_num ?? '');
      const lawTitle = String(row.law_title ?? '');
      const articleNum = String(row.article_num ?? '');
      const dedupeKey = `${getBaseLawKey(lawId, lawNum, lawTitle)}::${articleNum}`;
      if (seen.has(dedupeKey)) continue;
      seen.add(dedupeKey);

      results.push({
        law_id: lawId,
        law_num: lawNum,
        law_title: lawTitle,
        article_num: articleNum,
        hierarchy_path: String(row.hierarchy_path ?? ''),
        title: String(row.title ?? ''),
        matched_terms: matchedTerms,
        snippet: stripHtmlTags(String(row.snippet ?? '')).replace(/\s+/g, ' ').slice(0, 240),
      });
      if (results.length >= safeLimit) break;
    }

    return results;
  } finally {
    await stmt.close();
  }
}
