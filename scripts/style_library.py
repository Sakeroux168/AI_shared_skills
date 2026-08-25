#!/usr/bin/env python3
"""Deterministic lookup for the pinned GPT-Image2 style knowledge base."""

from __future__ import annotations

import argparse
import json
import re
from pathlib import Path
from typing import Any, Iterable


REPO_ROOT = Path(__file__).resolve().parents[1]
SOURCE_ROOT = REPO_ROOT / "sources" / "awesome-gpt-image-2" / "snapshot"
LIBRARY_PATH = SOURCE_ROOT / "data" / "style-library.json"
CASES_PATH = SOURCE_ROOT / "data" / "cases.json"
TEMPLATES_PATH = SOURCE_ROOT / "docs" / "templates.md"
SOURCE_LOCK_PATH = REPO_ROOT / "sources" / "awesome-gpt-image-2" / "source.lock.json"

EN_STOP = {
    "and",
    "for",
    "from",
    "into",
    "the",
    "this",
    "that",
    "use",
    "using",
    "with",
}
CJK_STOP = {"用于", "需要", "使用", "画面", "视觉", "主题", "进行"}

TEMPLATE_ALIASES = {
    "ui-screenshot-system": [
        "app",
        "ui",
        "界面",
        "仪表盘",
        "dashboard",
        "网页",
        "小程序",
        "截图",
    ],
    "infographic-engine": [
        "信息图",
        "图解",
        "流程图",
        "知识卡",
        "infographic",
        "diagram",
        "timeline",
        "时间线",
    ],
    "scientific-scale-diagram": ["微观", "宏观", "尺度", "倍率", "scale diagram"],
    "poster-layout-system": [
        "海报",
        "poster",
        "活动主视觉",
        "电影海报",
        "音乐节",
        "封面",
    ],
    "sports-campaign-poster": ["运动员", "体育", "球鞋", "sports campaign"],
    "conceptual-typography-poster": ["字体海报", "文字主视觉", "typography poster"],
    "ink-double-exposure-poster": ["水墨", "双重曝光", "ink", "double exposure"],
    "nature-science-poster": ["自然科普海报", "自然科学海报"],
    "product-commerce-visual": [
        "商品",
        "电商",
        "产品主图",
        "商品主图",
        "详情页",
        "包装",
        "product hero",
        "e-commerce",
    ],
    "personalized-beauty-report": ["美妆报告", "肤质", "导购助手", "beauty report"],
    "brand-identity-package": ["品牌身份", "vi", "logo 系统", "brand identity"],
    "brand-touchpoint-board": ["品牌触点", "campaign board", "应用样机"],
    "architecture-space": ["建筑", "室内", "空间规划", "architecture", "interior"],
    "realistic-photography": [
        "写实摄影",
        "人像摄影",
        "写真",
        "摄影棚",
        "镜头",
        "photography",
        "portrait photo",
    ],
    "street-accident-moment": ["抓拍", "意外瞬间", "手机纪实", "candid street"],
    "illustration-art-style": ["插画", "水彩", "绘画", "illustration"],
    "character-design-sheet": ["角色设定", "三视图", "动作表", "character sheet"],
    "3d-collectible-toy": ["收藏玩具", "手办", "盲盒", "3d toy"],
    "scene-storytelling": ["场景叙事", "分镜", "故事场景", "storyboard"],
    "history-classical-themes": ["古风", "历史题材", "长卷", "classical history"],
    "document-publishing": ["文档排版", "出版物", "手册", "document layout"],
    "concept-product-breakdown": ["产品拆解", "研发拆解", "爆炸图", "product breakdown"],
}

STYLE_ALIASES = {
    "3D": ["3d", "三维", "立体", "玩具", "手办"],
    "Brand": ["品牌", "logo", "vi"],
    "Character": ["角色", "人物", "人设"],
    "Classical": ["古典", "古风", "历史"],
    "Illustration": ["插画", "绘画", "水彩"],
    "Infographic": ["信息图", "图解", "流程图"],
    "Poster": ["海报", "封面", "poster"],
    "Product": ["商品", "产品", "包装", "电商"],
    "Realistic": ["写实", "真实", "摄影", "照片", "photorealistic"],
    "UI": ["ui", "界面", "仪表盘", "app", "dashboard"],
}

SCENE_ALIASES = {
    "Commerce": ["商业", "商品", "电商", "广告", "品牌", "campaign"],
    "Creative": ["创意", "实验", "concept"],
    "Education": ["教育", "科普", "学习", "知识"],
    "Fashion": ["时尚", "服饰", "美妆", "人像"],
    "Food": ["食品", "饮料", "咖啡", "茶", "餐厅"],
    "History": ["历史", "古代", "朝代", "古风"],
    "Social": ["社媒", "朋友圈", "社交", "social"],
    "Story": ["故事", "叙事", "分镜", "世界观"],
    "Tech": ["科技", "技术", "数据", "ai", "app"],
    "Travel": ["旅行", "城市", "地图", "街道"],
}


def load_json(path: Path) -> Any:
    with path.open("r", encoding="utf-8") as handle:
        return json.load(handle)


def locked_commit() -> str:
    return str(load_json(SOURCE_LOCK_PATH)["commit"])


def flatten_strings(value: Any) -> Iterable[str]:
    if isinstance(value, str):
        yield value
    elif isinstance(value, dict):
        for item in value.values():
            yield from flatten_strings(item)
    elif isinstance(value, list):
        for item in value:
            yield from flatten_strings(item)


def _cjk_terms(text: str) -> set[str]:
    terms: set[str] = set()
    for chunk in re.findall(r"[\u3400-\u9fff]+", text):
        for size in range(2, min(7, len(chunk) + 1)):
            for index in range(0, len(chunk) - size + 1):
                term = chunk[index : index + size]
                if term not in CJK_STOP:
                    terms.add(term)
    return terms


def _english_terms(text: str) -> set[str]:
    return {
        word
        for word in re.findall(r"[a-z0-9][a-z0-9&+-]*", text.casefold())
        if len(word) >= 2 and word not in EN_STOP
    }


def term_score(query: str, text: str, weight: int) -> tuple[int, list[str]]:
    normalized = query.casefold()
    matched: list[str] = []
    score = 0
    for term in sorted(_english_terms(text) | _cjk_terms(text), key=len, reverse=True):
        if term.casefold() in normalized:
            matched.append(term)
            score += weight * max(1, min(len(term), 6))
    return score, matched[:8]


def alias_score(query: str, aliases: Iterable[str]) -> tuple[int, list[str]]:
    normalized = query.casefold()
    matched = [alias for alias in aliases if alias.casefold() in normalized]
    return sum(35 + min(len(alias), 12) for alias in matched), matched


def _template_score(query: str, template: dict[str, Any]) -> tuple[int, list[str]]:
    score, reasons = alias_score(query, TEMPLATE_ALIASES.get(template["id"], []))
    weighted_fields = [
        (template.get("title"), 8),
        (template.get("category"), 7),
        (template.get("styles"), 6),
        (template.get("scenes"), 5),
        (template.get("tags"), 6),
        (template.get("useWhen"), 4),
        (template.get("guidance"), 1),
    ]
    for value, weight in weighted_fields:
        field_text = " ".join(flatten_strings(value))
        field_score, matched = term_score(query, field_text, weight)
        score += field_score
        reasons.extend(matched)
    return score, list(dict.fromkeys(reasons))[:12]


def match_template(query: str, library: dict[str, Any] | None = None) -> dict[str, Any]:
    library = library or load_json(LIBRARY_PATH)
    ranked = []
    for template in library["templates"]:
        score, reasons = _template_score(query, template)
        ranked.append((score, template["id"], reasons, template))
    ranked.sort(key=lambda item: (-item[0], item[1]))
    score, _, reasons, template = ranked[0]
    return {
        "template": template,
        "score": score,
        "matched_terms": reasons,
        "alternatives": [
            {"id": item[3]["id"], "score": item[0]}
            for item in ranked[1:3]
        ],
    }


def _best_tag(
    query: str,
    allowed_values: list[str],
    aliases: dict[str, list[str]],
    preferred: list[str],
) -> str:
    ranked = []
    for value in allowed_values:
        score, _ = alias_score(query, aliases.get(value, [value]))
        if value in preferred:
            score += 8
        ranked.append((score, value))
    ranked.sort(key=lambda item: (-item[0], item[1]))
    if ranked and ranked[0][0] > 0:
        return ranked[0][1]
    return preferred[0] if preferred else allowed_values[0]


def select_tags(query: str, template: dict[str, Any], library: dict[str, Any]) -> tuple[str, str]:
    style_values = [item["value"] for item in library["styles"]]
    scene_values = [item["value"] for item in library["scenes"]]
    style = _best_tag(query, style_values, STYLE_ALIASES, template.get("styles", []))
    scene = _best_tag(query, scene_values, SCENE_ALIASES, template.get("scenes", []))
    return style, scene


def _localized(value: Any, language: str) -> Any:
    if isinstance(value, dict):
        return value.get(language) or value.get("en") or next(iter(value.values()), "")
    return value


def build_prompt(
    query: str,
    *,
    aspect_ratio: str = "1:1",
    output_format: str = "high-resolution image",
) -> dict[str, Any]:
    library = load_json(LIBRARY_PATH)
    result = match_template(query, library)
    template = result["template"]
    language = "zh" if re.search(r"[\u3400-\u9fff]", query) else "en"
    style, scene = select_tags(query, template, library)
    guidance = _localized(template.get("guidance", {}), language) or []
    pitfalls = _localized(template.get("pitfalls", {}), language) or []
    while len(guidance) < 2:
        guidance.append("Keep hierarchy, layout, and focal subject explicit.")
    if language == "zh":
        text_rule = "逐字保留用户指定文字；未指定时只使用必要短标签，并保证清晰可读。"
        material_rule = f"采用 {style} 风格并服务于 {scene} 场景；明确材质、光线和色彩关系。"
        constraint_prefix = "避免："
    else:
        text_rule = "Preserve user-specified text exactly; otherwise use only necessary short, legible labels."
        material_rule = f"Use the {style} style for a {scene} scene; specify materials, lighting, and palette."
        constraint_prefix = "Avoid: "
    blocks = {
        "subject_and_task": query.strip(),
        "composition_and_layout": guidance[0],
        "visual_style_and_materials": material_rule,
        "text_and_label_requirements": text_rule,
        "aspect_ratio_and_output_format": f"{aspect_ratio}; {output_format}.",
        "constraints_and_negative_details": constraint_prefix + " ".join(pitfalls or [guidance[1]]),
    }
    return {
        "template_id": template["id"],
        "template_name": _localized(template["title"], language),
        "category": template["category"],
        "styles": [style],
        "scenes": [scene],
        "example_case_ids": template.get("exampleCases", []),
        "matched_terms": result["matched_terms"],
        "alternatives": result["alternatives"],
        "prompt": blocks,
        "source": {
            "level": "full pinned source",
            "library": str(LIBRARY_PATH.relative_to(REPO_ROOT)),
            "templates": str(TEMPLATES_PATH.relative_to(REPO_ROOT)),
            "commit": locked_commit(),
        },
    }


def search_cases(query: str, limit: int = 5) -> list[dict[str, Any]]:
    library = load_json(LIBRARY_PATH)
    cases = load_json(CASES_PATH)["cases"]
    template = match_template(query, library)["template"]
    ranked = []
    for case in cases:
        searchable = " ".join(
            flatten_strings(
                {
                    "title": case.get("title"),
                    "category": case.get("category"),
                    "styles": case.get("styles"),
                    "scenes": case.get("scenes"),
                    "preview": case.get("promptPreview"),
                }
            )
        )
        score, reasons = term_score(query, searchable, 2)
        if case.get("category") == template.get("category"):
            score += 20
        score += 4 * len(set(case.get("styles", [])) & set(template.get("styles", [])))
        score += 3 * len(set(case.get("scenes", [])) & set(template.get("scenes", [])))
        ranked.append((score, -int(case["id"]), reasons, case))
    ranked.sort(key=lambda item: (-item[0], item[1]))
    return [
        {
            "id": item[3]["id"],
            "title": item[3]["title"],
            "category": item[3]["category"],
            "styles": item[3].get("styles", []),
            "scenes": item[3].get("scenes", []),
            "sourceLabel": item[3].get("sourceLabel"),
            "sourceUrl": item[3].get("sourceUrl"),
            "matched_terms": item[2],
        }
        for item in ranked[:limit]
    ]


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    subparsers = parser.add_subparsers(dest="command", required=True)

    match_parser = subparsers.add_parser("match", help="Classify a query")
    match_parser.add_argument("--query", required=True)

    build_parser = subparsers.add_parser("build", help="Build a structured prompt")
    build_parser.add_argument("--query", required=True)
    build_parser.add_argument("--aspect-ratio", default="1:1")
    build_parser.add_argument("--output-format", default="high-resolution image")

    cases_parser = subparsers.add_parser("search-cases", help="Find close example cases")
    cases_parser.add_argument("--query", required=True)
    cases_parser.add_argument("--limit", type=int, default=5)

    args = parser.parse_args()
    if args.command == "match":
        match = match_template(args.query)
        output = {
            "template_id": match["template"]["id"],
            "category": match["template"]["category"],
            "score": match["score"],
            "matched_terms": match["matched_terms"],
            "alternatives": match["alternatives"],
        }
    elif args.command == "build":
        output = build_prompt(
            args.query,
            aspect_ratio=args.aspect_ratio,
            output_format=args.output_format,
        )
    else:
        output = search_cases(args.query, args.limit)
    print(json.dumps(output, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
