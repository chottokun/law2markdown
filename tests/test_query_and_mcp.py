"""Tests for query engine and MCP server."""

import json
from pathlib import Path

from law2markdown.converter import convert_law_xml_content
from law2markdown.mcp_server import handle_mcp_request
from law2markdown.query import get_article, get_hierarchy, lookup_term, trace_references

SAMPLE_LAW_XML = """<?xml version="1.0" encoding="UTF-8"?>
<Law Era="Reiwa" Year="5" Num="100" LawType="Act" Lang="ja">
  <LawNum>令和五年法律第百号</LawNum>
  <LawBody>
    <LawTitle>エージェント法</LawTitle>
    <MainProvision>
      <Chapter Num="1">
        <ChapterTitle>第一章　総則</ChapterTitle>
        <Article Num="1">
          <ArticleCaption>（目的）</ArticleCaption>
          <ArticleTitle>第一条</ArticleTitle>
          <Paragraph Num="1">
            <ParagraphNum/>
            <ParagraphSentence>
              <Sentence>この法律において「AI」とは、人工知能をいう。</Sentence>
            </ParagraphSentence>
          </Paragraph>
          <Paragraph Num="2">
            <ParagraphNum>２</ParagraphNum>
            <ParagraphSentence>
              <Sentence>AIの運用は次条の規定に従う。</Sentence>
            </ParagraphSentence>
          </Paragraph>
        </Article>
        <Article Num="2">
          <ArticleCaption>（適用の基準）</ArticleCaption>
          <ArticleTitle>第二条</ArticleTitle>
          <Paragraph Num="1">
            <ParagraphNum/>
            <ParagraphSentence>
              <Sentence>前条のAIは、安全に運用されなければならない。</Sentence>
            </ParagraphSentence>
          </Paragraph>
        </Article>
      </Chapter>
    </MainProvision>
  </LawBody>
</Law>"""


def test_query_functions(tmp_path: Path):
    convert_law_xml_content(SAMPLE_LAW_XML, str(tmp_path), law_id="505AC0000000100")

    # 1. get_article (whole article)
    res1 = get_article(tmp_path, "エージェント法", "1")
    assert res1["found"] is True
    assert res1["title"] == "エージェント法 第一条 （目的）"
    assert "人工知能をいう。" in res1["body"]

    # 1-b. get_article (specific paragraph slice)
    res1_p2 = get_article(tmp_path, "エージェント法", "1", paragraph_num=2)
    assert res1_p2["found"] is True
    assert "次条の規定に従う" in res1_p2["body"]
    assert "人工知能をいう" not in res1_p2["body"]

    # 2. get_hierarchy
    res2 = get_hierarchy(tmp_path, "エージェント法", "1")
    assert res2["found"] is True
    assert "第一章　総則" in res2["hierarchy_path"]
    assert len(res2["sibling_articles"]) >= 2

    # 3. trace_references
    res3 = trace_references(tmp_path, "エージェント法", "1", direction="both")
    assert res3["found"] is True
    assert any("第二条" in ref["title"] for ref in res3["outbound_references"])
    assert any("第二条" in ref["title"] for ref in res3["inbound_references"])

    # 4. lookup_term
    res4 = lookup_term(tmp_path, "エージェント法", "AI")
    assert res4["found"] is True
    assert res4["term"] == "AI"
    assert "人工知能をいう" in res4["definition"]


def test_mcp_protocol(tmp_path: Path):
    convert_law_xml_content(SAMPLE_LAW_XML, str(tmp_path), law_id="505AC0000000100")

    # 1. tools/list
    list_req = {"jsonrpc": "2.0", "id": 1, "method": "tools/list", "params": {}}
    list_res_str = handle_mcp_request(json.dumps(list_req), kb_dir=str(tmp_path))
    list_res = json.loads(list_res_str)
    assert "result" in list_res
    tool_names = [t["name"] for t in list_res["result"]["tools"]]
    assert "get_article" in tool_names
    assert "get_hierarchy" in tool_names
    assert "trace_references" in tool_names
    assert "lookup_term" in tool_names

    # 2. tools/call get_article
    call_req = {
        "jsonrpc": "2.0",
        "id": 2,
        "method": "tools/call",
        "params": {
            "name": "get_article",
            "arguments": {"law": "エージェント法", "article_num": "1", "paragraph_num": 2},
        },
    }
    call_res_str = handle_mcp_request(json.dumps(call_req), kb_dir=str(tmp_path))
    call_res = json.loads(call_res_str)
    assert "result" in call_res
    text_content = call_res["result"]["content"][0]["text"]
    assert "次条の規定に従う" in text_content
