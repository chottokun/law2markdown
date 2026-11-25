import { Chart } from 'chart.js';
import { describe, expect, it } from 'vitest';
import './AnalyticsTab';

describe('AnalyticsTab Chart.js registration', () => {
  it('registers the bar controller and required scales/elements', () => {
    expect(Chart.registry.getController('bar')).toBeDefined();
    expect(Chart.registry.getScale('category')).toBeDefined();
    expect(Chart.registry.getScale('linear')).toBeDefined();
    expect(Chart.registry.getElement('bar')).toBeDefined();
  });
});
