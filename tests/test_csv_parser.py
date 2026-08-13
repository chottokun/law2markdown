"""Tests for CSV parser."""

from law2markdown.parser.csv_parser import parse_law_csv_content


def test_parse_law_csv_content():
    csv_text = (
        "﻿法令種別,法令番号,法令名,法令名読み,旧法令名,公布日,改正法令名,改正法令番号,改正法令公布日,施行日,施行日備考,法令ID,本文URL,未施行\n"
        "法律,昭和二十一年法律第二十五号,労働関係調整法,ろうどうかんけいちょうせいほう,,昭和二十一年九月二十七日,行政不服審査法の施行に伴う関係法律の整備等に関する法律,平成二十六年法律第六十九号,平成二十六年六月十三日,平成二十八年四月一日,,321AC0000000025,https://laws.e-gov.go.jp/law/321AC0000000025/20160401_426AC0000000069,\n"  # noqa: E501
        "法律,昭和二十二年法律第四十九号,労働基準法,ろうどうきじゅんほう,,昭和二十二年四月七日,労働者災害補償保険法等の一部を改正する法律,令和八年法律第六十号,令和八年七月十七日,令和九年四月一日,,322AC0000000049,https://laws.e-gov.go.jp/law/322AC0000000049/20270401_508AC0000000060,○\n"  # noqa: E501
    )
    csv_map = parse_law_csv_content(csv_text)

    key1 = "321AC0000000025_20160401_426AC0000000069"
    assert key1 in csv_map
    info1 = csv_map[key1]
    assert info1["title_kana"] == "ろうどうかんけいちょうせいほう"
    assert info1["promulgate_date"] == "昭和二十一年九月二十七日"
    assert info1["enforce_date"] == "平成二十八年四月一日"
    assert info1["is_unexecuted"] is False

    key2 = "322AC0000000049_20270401_508AC0000000060"
    assert key2 in csv_map
    info2 = csv_map[key2]
    assert info2["is_unexecuted"] is True
