export type TabId = 'viewer' | 'graph' | 'diff' | 'glossary' | 'analytics';

export type DbStatus = 'idle' | 'initializing' | 'ready' | 'error';

export interface LawCatalogEntry {
  law_id: string;
  law_num: string;
  law_title: string;
  article_count: number;
}

export interface ArticleSummary {
  law_id: string;
  article_num: string;
  hierarchy_path: string;
  title: string;
  outbound_references: string[];
  inbound_references: string[];
  defined_terms: string[];
}

export interface ArticleDetail extends ArticleSummary {
  law_num: string;
  law_title: string;
  content: string;
  child_anchors_json: string;
}

export interface SearchResultEntry {
  law_id: string;
  law_num: string;
  law_title: string;
  article_num: string;
  hierarchy_path: string;
  title: string;
  snippet: string;
}

export interface AnalyticsSummary {
  totalArticles: number;
  totalLaws: number;
  totalLawVersions: number;
  totalOutboundEdges: number;
  totalDefinedTerms: number;
  eraDistribution: { era: string; count: number }[];
  topLawsByArticles: { law_id: string; law_title: string; law_num: string; count: number }[];
  topLawsByTerms: { law_id: string; law_title: string; count: number }[];
}

export interface SqlQueryResult {
  columns: string[];
  rows: Record<string, unknown>[];
  elapsedMs: number;
  truncated: boolean;
}

export interface ToastMessage {
  id: number;
  kind: 'info' | 'success' | 'error';
  text: string;
}

export interface ArticleContentRow {
  article_num: string;
  hierarchy_path: string;
  title: string;
  content: string;
}

export interface PopularTermEntry {
  term: string;
  law_count: number;
  occurrence_count: number;
}

export interface TermDefinitionHit {
  law_id: string;
  law_num: string;
  law_title: string;
  article_num: string;
  hierarchy_path: string;
  title: string;
  matched_terms: string[];
  snippet: string;
}
