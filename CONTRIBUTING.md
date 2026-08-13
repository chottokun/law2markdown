# CONTRIBUTING

law2markdown プロジェクトへの貢献ガイドラインです。

## 開発フロー

1. **ブランチ運用**:
   - `main` ブランチへの直接コミットは行わず、`feature/xxx` や `fix/xxx` ブランチを作成してください。
2. **コミット規約 (Conventional Commits)**:
   - コミットメッセージには `feat:`, `fix:`, `docs:`, `test:`, `refactor:`, `chore:` などのプレフィクスを付与してください。
3. **TDD (テスト駆動開発)**:
   - 新機能の追加や修正の際は、先にテストケース (`tests/`) を作成して並行して開発を行ってください。
4. **品質チェック**:
   - コミット前に `uv run ruff check`, `uv run ruff format --check`, `uv run pytest`, `uv audit` をすべてパスさせてください。
