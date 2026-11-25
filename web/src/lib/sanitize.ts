import DOMPurify from 'dompurify';
import { marked } from 'marked';

marked.setOptions({
  gfm: true,
  breaks: true,
});

/**
 * 条文 Markdown（HTML <table> や <a id="..."> を含む）を安全に HTML 化する。
 * すべての生成 HTML は DOMPurify でサニタイズし、XSS を防止する。
 */
export function renderSafeMarkdown(markdown: string): string {
  const rawHtml = marked.parse(markdown, { async: false });
  return DOMPurify.sanitize(rawHtml, {
    USE_PROFILES: { html: true },
    ADD_ATTR: ['id'],
  });
}

/**
 * 検索スニペット表示用に Markdown 中の HTML アンカー等を除去して整形する。
 */
export function stripHtmlTags(text: string): string {
  return text.replace(/<[^>]*>/g, '').trim();
}
