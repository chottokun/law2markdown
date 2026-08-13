"""CLI entrypoint for law2markdown."""

import argparse
import sys

from law2markdown import __version__
from law2markdown.converter import convert_law_xml_file, convert_law_zip_file


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
        elif args.command == "convert-zip":
            out_paths = convert_law_zip_file(
                zip_path=args.zip_path,
                output_dir=args.output_dir,
            )
            print(f"ZIP 一括変換完了: {len(out_paths)} 件の法令を出力しました -> {args.output_dir}")
        return 0
    except Exception as e:
        print(f"エラーが発生しました: {e}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
