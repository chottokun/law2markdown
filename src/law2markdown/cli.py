"""CLI entrypoint for law2markdown."""

import argparse
import sys

from law2markdown import __version__
from law2markdown.converter import convert_law_xml_file, convert_law_zip_file
from law2markdown.mcp_server import run_mcp_server
from law2markdown.query import get_article, get_hierarchy, lookup_term, trace_references
from law2markdown.validator import validate_directory_links


def print_audit_report(output_dir: str) -> bool:
    """Validate links and print audit summary."""
    report = validate_directory_links(output_dir)

    print("\n--- 📊 変換・整合性監査レポート ---")
    print(f"・対象ディレクトリ: {output_dir}")
    print(f"・総ファイル数: {report.total_files_checked:,} 件")
    if report.total_laws:
        print(
            f"  - 収録法令: {report.total_laws:,} 件 "
            f"(条文: {report.total_articles:,} 件, "
            f"附則: {report.total_suppls:,} 件, "
            f"別表/様式: {report.total_appendices:,} 件)"
        )
    print(f"・検証リンク数: {report.total_links_checked:,} 箇所")

    if report.is_valid:
        print("・リンク完全性検証: ✅ PASS (リンク切れ: 0 件)\n")
        return True
    else:
        print(f"・リンク完全性検証: ❌ FAIL (リンク切れ: {len(report.broken_links)} 件)")
        for file_path, link_target, reason in report.broken_links[:10]:
            print(f"   [!] {file_path} -> '{link_target}' ({reason})")
        if len(report.broken_links) > 10:
            print(f"   ... 他 {len(report.broken_links) - 10} 件")
        print()
        return False


def main() -> int:
    """CLI main function."""
    parser = argparse.ArgumentParser(
        prog="law2md",
        description="e-Gov 法令 XML から Markdown への変換ツール",
    )
    parser.add_argument("--version", action="version", version=f"%(prog)s {__version__}")

    subparsers = parser.add_subparsers(dest="command", help="サブコマンド")

    # convert コマンド
    convert_parser = subparsers.add_parser("convert", help="単一 XML ファイルの変換")
    convert_parser.add_argument("input_path", help="入力 XML ファイルのパス")
    convert_parser.add_argument("-o", "--output-dir", default="./output", help="出力ディレクトリ")
    convert_parser.add_argument("--law-id", default="", help="法令ID (ディレクトリ名)")

    # convert-zip コマンド
    zip_parser = subparsers.add_parser("convert-zip", help="ZIP ファイル内 XML の一括変換")
    zip_parser.add_argument("zip_path", help="入力 ZIP ファイルのパス")
    zip_parser.add_argument("-o", "--output-dir", default="./output", help="出力ディレクトリ")

    # query コマンド
    query_parser = subparsers.add_parser("query", help="変換済ナレッジベースに対する法探索クエリ")
    query_sub = query_parser.add_subparsers(dest="query_cmd", help="クエリ種別")

    q_art = query_sub.add_parser("get-article", help="条文または項の本文取得")
    q_art.add_argument("law", help="法令名または法令ID")
    q_art.add_argument("article_num", help="条番号")
    q_art.add_argument("-p", "--paragraph-num", type=int, default=None, help="項番号")
    q_art.add_argument("-d", "--kb-dir", default="./output", help="ナレッジベースディレクトリ")

    q_hier = query_sub.add_parser("get-hierarchy", help="条文の上位階層・関連条文取得")
    q_hier.add_argument("law", help="法令名または法令ID")
    q_hier.add_argument("article_num", help="条番号")
    q_hier.add_argument("-d", "--kb-dir", default="./output", help="ナレッジベースディレクトリ")

    q_ref = query_sub.add_parser("trace-references", help="条文の参照関係グラフ走査")
    q_ref.add_argument("law", help="法令名または法令ID")
    q_ref.add_argument("article_num", help="条番号")
    q_ref.add_argument("--direction", choices=["outbound", "inbound", "both"], default="both")
    q_ref.add_argument("-d", "--kb-dir", default="./output", help="ナレッジベースディレクトリ")

    q_term = query_sub.add_parser("lookup-term", help="法定用語の定義照会")
    q_term.add_argument("law", help="法令名または法令ID")
    q_term.add_argument("term", help="専門用語")
    q_term.add_argument("-d", "--kb-dir", default="./output", help="ナレッジベースディレクトリ")

    # mcp コマンド
    mcp_parser = subparsers.add_parser(
        "mcp", help="Agentic RAG 用 MCP (Model Context Protocol) サーバー起動"
    )
    mcp_parser.add_argument("-d", "--kb-dir", default="./output", help="ナレッジベースディレクトリ")

    # dataset コマンド
    ds_parser = subparsers.add_parser(
        "dataset", help="Hugging Face / Releases 向けデータセット構築・配信"
    )
    ds_sub = ds_parser.add_subparsers(dest="dataset_cmd", help="データセット操作")

    ds_build = ds_sub.add_parser("build", help="主要法令の取得・変換・Parquet/アーカイブ構築")
    ds_build.add_argument(
        "--scope", choices=["core", "custom"], default="core", help="法令取得スコープ"
    )
    ds_build.add_argument("-o", "--output-dir", default="./output/legal_kb", help="KB出力先")
    ds_build.add_argument(
        "--parquet-out", default="./output/laws_articles.parquet", help="Parquet出力先"
    )
    ds_build.add_argument(
        "--archive-out", default="./output/laws-markdown.tar.zst", help="Archive出力先"
    )
    ds_build.add_argument("--upload-hf", action="store_true", help="Hugging Faceへ自動アップロード")
    ds_build.add_argument(
        "--repo-id", default="Chottokun/japan-laws-md", help="Hugging Face repo_id"
    )
    ds_build.add_argument(
        "--token", default="", help="Hugging Face トークン (未指定時は HF_TOKEN 環境変数)"
    )
    ds_build.add_argument("--max-laws", type=int, default=None, help="最大処理法令数 (テスト用)")

    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        return 1

    try:
        if args.command == "convert":
            out_path = convert_law_xml_file(
                xml_path=args.input_path,
                output_dir=args.output_dir,
                law_id=args.law_id,
            )
            print(f"変換完了: {out_path}")
            is_valid = print_audit_report(args.output_dir)
            return 0 if is_valid else 1
        elif args.command == "convert-zip":
            out_paths = convert_law_zip_file(
                zip_path=args.zip_path,
                output_dir=args.output_dir,
            )
            print(f"ZIP 一括変換完了: {len(out_paths)} 件の法令を出力しました -> {args.output_dir}")
            is_valid = print_audit_report(args.output_dir)
            return 0 if is_valid else 1
        elif args.command == "query":
            import json

            res: dict = {}
            if args.query_cmd == "get-article":
                res = get_article(
                    args.kb_dir, args.law, args.article_num, paragraph_num=args.paragraph_num
                )
            elif args.query_cmd == "get-hierarchy":
                res = get_hierarchy(args.kb_dir, args.law, args.article_num)
            elif args.query_cmd == "trace-references":
                res = trace_references(
                    args.kb_dir, args.law, args.article_num, direction=args.direction
                )
            elif args.query_cmd == "lookup-term":
                res = lookup_term(args.kb_dir, args.law, args.term)
            else:
                query_parser.print_help()
                return 1

            if res.get("body"):
                print(res["body"])
            else:
                print(json.dumps(res, ensure_ascii=False, indent=2))
            return 0 if res.get("found", False) else 1
        elif args.command == "mcp":
            run_mcp_server(kb_dir=args.kb_dir)
            return 0
        elif args.command == "dataset":
            import os
            from pathlib import Path

            from law2markdown.dataset import (
                CORE_LAWS,
                collect_article_records,
                create_markdown_tar_zst,
                download_law_xml,
                export_articles_parquet,
                generate_dataset_card,
                upload_to_huggingface,
            )

            if args.dataset_cmd == "build":
                kb_path = Path(args.output_dir)
                raw_xml_dir = Path("./tmp/raw_xml")
                raw_xml_dir.mkdir(parents=True, exist_ok=True)

                laws_to_process = list(CORE_LAWS.items())
                if args.max_laws:
                    laws_to_process = laws_to_process[: args.max_laws]

                print(f"📦 データセット構築開始: {len(laws_to_process)} 件の法令を対象")
                for i, (law_id, law_name) in enumerate(laws_to_process, 1):
                    print(
                        f"[{i}/{len(laws_to_process)}] ダウンロード & 変換中: "
                        f"{law_name} ({law_id})..."
                    )
                    xml_file = raw_xml_dir / f"{law_id}.xml"
                    download_law_xml(law_id, xml_file)
                    convert_law_xml_file(str(xml_file), str(kb_path), law_id=law_id)

                print("📊 条文レコードの集約と Parquet 出力中...")
                records = collect_article_records(kb_path)
                parquet_path = export_articles_parquet(records, Path(args.parquet_out))
                print(f"✅ Parquet 作成完了: {parquet_path} ({len(records)} 条文)")

                print("🗜️ Markdown アーカイブの圧縮中...")
                archive_path = create_markdown_tar_zst(kb_path, Path(args.archive_out))
                print(f"✅ アーカイブ作成完了: {archive_path}")

                if args.upload_hf:
                    hf_token = args.token or os.environ.get("HF_TOKEN", "")
                    if not hf_token:
                        print("❌ エラー: Hugging Face トークンが未指定です (HF_TOKEN)")
                        return 1
                    print(f"🚀 Hugging Face ({args.repo_id}) へアップロード中...")
                    card_text = generate_dataset_card(
                        law_count=len(laws_to_process),
                        article_count=len(records),
                    )
                    files_to_upload = {
                        archive_path.name: archive_path,
                        parquet_path.name: parquet_path,
                    }
                    upload_to_huggingface(
                        repo_id=args.repo_id,
                        token=hf_token,
                        files=files_to_upload,
                        dataset_card_content=card_text,
                    )
                    print(
                        f"🎉 Hugging Face 公開完了: https://huggingface.co/datasets/{args.repo_id}"
                    )

                return 0
            else:
                ds_parser.print_help()
                return 1
        return 0
    except Exception as e:
        print(f"エラーが発生しました: {e}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
