export const HF_DATASET_ID = 'Chottokun/japan-laws-md';
export const HF_DATASET_URL = `https://huggingface.co/datasets/${HF_DATASET_ID}`;
export const GITHUB_REPO_URL = 'https://github.com/chottokun/law2markdown';
export const PARQUET_URL = `https://huggingface.co/datasets/${HF_DATASET_ID}/resolve/main/laws_articles.parquet`;
export const PARQUET_VIRTUAL_NAME = 'laws_articles.parquet';

export interface CoreLawEntry {
  idPrefix: string;
  label: string;
  title: string;
}

export const CORE_LAWS: CoreLawEntry[] = [
  { idPrefix: '321CONSTITUTION', label: '憲法', title: '日本国憲法' },
  { idPrefix: '129AC0000000089', label: '民法', title: '民法' },
  { idPrefix: '140AC0000000045', label: '刑法', title: '刑法' },
  { idPrefix: '132AC0000000048', label: '商法', title: '商法' },
  { idPrefix: '417AC0000000086', label: '会社法', title: '会社法' },
  { idPrefix: '323AC0000000131', label: '刑事訴訟法', title: '刑事訴訟法' },
  { idPrefix: '408AC0000000109', label: '民事訴訟法', title: '民事訴訟法' },
  { idPrefix: '322AC0000000049', label: '労働基準法', title: '労働基準法' },
  { idPrefix: '405AC0000000088', label: '行政手続法', title: '行政手続法' },
  {
    idPrefix: '415AC0000000057',
    label: '個人情報保護法',
    title: '個人情報の保護に関する法律',
  },
  { idPrefix: '345AC0000000048', label: '著作権法', title: '著作権法' },
  { idPrefix: '334AC0000000121', label: '特許法', title: '特許法' },
];

export interface SqlPreset {
  id: string;
  label: string;
  description: string;
  sql: string;
}

export const SQL_PRESETS: SqlPreset[] = [
  {
    id: 'top-laws',
    label: '条文数 Top 15 法令',
    description: '収録条文数が多い上位15法令を集計',
    sql: `SELECT
  law_title,
  law_num,
  COUNT(*) AS article_count
FROM laws_articles
GROUP BY law_id, law_title, law_num
ORDER BY article_count DESC
LIMIT 15`,
  },
  {
    id: 'longest-articles',
    label: '最長条文 Top 20',
    description: '文字数が最も多い条文ランキング',
    sql: `SELECT
  law_title,
  article_num,
  title,
  LENGTH(content) AS char_length
FROM laws_articles
ORDER BY char_length DESC
LIMIT 20`,
  },
  {
    id: 'most-referenced',
    label: '被参照数 Top 20 条文',
    description: '同一法令・他条文から最も多く参照されている条文',
    sql: `SELECT
  law_title,
  article_num,
  title,
  LEN(inbound_references) AS inbound_count,
  LEN(outbound_references) AS outbound_count
FROM laws_articles
ORDER BY inbound_count DESC
LIMIT 20`,
  },
  {
    id: 'penalty-articles',
    label: '「懲役」を含む規定の抽出',
    description: '罰則規定の多い法令トップ20',
    sql: `SELECT
  law_title,
  COUNT(*) AS penalty_articles
FROM laws_articles
WHERE content LIKE '%懲役%' OR content LIKE '%拘禁刑%'
GROUP BY law_title
ORDER BY penalty_articles DESC
LIMIT 20`,
  },
  {
    id: 'defined-terms-sample',
    label: '定義用語を多く持つ条文',
    description: '定義規定が集中している条文一覧',
    sql: `SELECT
  law_title,
  article_num,
  LEN(defined_terms) AS term_count,
  defined_terms
FROM laws_articles
WHERE LEN(defined_terms) > 0
ORDER BY term_count DESC
LIMIT 20`,
  },
];
