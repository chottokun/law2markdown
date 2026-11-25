import { fireEvent, render, screen, waitFor } from '@testing-library/react';
import { beforeEach, describe, expect, it, vi } from 'vitest';
import type { PopularTermEntry, TermDefinitionHit } from '../lib/types';

const { fetchTopDefinedTermsMock, searchDefinedTermsMock } = vi.hoisted(() => ({
  fetchTopDefinedTermsMock: vi.fn(),
  searchDefinedTermsMock: vi.fn(),
}));

vi.mock('../lib/queries', () => ({
  fetchTopDefinedTerms: fetchTopDefinedTermsMock,
  searchDefinedTerms: searchDefinedTermsMock,
}));

import { GlossaryTab } from './GlossaryTab';

const popular: PopularTermEntry[] = [
  { term: '労働者', law_count: 15, occurrence_count: 20 },
  { term: '個人情報', law_count: 8, occurrence_count: 10 },
];

const hits: TermDefinitionHit[] = [
  {
    law_id: '322AC0000000049',
    law_num: '昭和二十二年法律第四十九号',
    law_title: '労働基準法',
    article_num: '9',
    hierarchy_path: '労働基準法 > 第一章 > 第九条',
    title: '労働基準法 第九条',
    matched_terms: ['労働者'],
    snippet: 'この法律で「労働者」とは、職業の種類を問わず...',
  },
];

describe('GlossaryTab', () => {
  beforeEach(() => {
    fetchTopDefinedTermsMock.mockResolvedValue(popular);
    searchDefinedTermsMock.mockResolvedValue(hits);
  });

  it('loads popular terms, displays definition cards, and jumps to viewer', async () => {
    const onOpenInViewer = vi.fn();
    render(<GlossaryTab onOpenInViewer={onOpenInViewer} onNotify={vi.fn()} />);

    await waitFor(() => {
      expect(screen.getByText('労働基準法')).toBeInTheDocument();
    });

    expect(screen.getByText('個人情報 (8法令)')).toBeInTheDocument();
    fireEvent.click(screen.getByRole('button', { name: '条文を開く' }));
    expect(onOpenInViewer).toHaveBeenCalledWith('322AC0000000049', '9');
  });
});
