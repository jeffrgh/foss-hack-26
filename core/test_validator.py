"""
test_validator.py
=================
Test suite for validator.py.  Run with:  python -m pytest test_validator.py -v

Covers:
  - Original 12 baseline cases
  - 10 new cases from Person B's JSON files (patterns discovered in the audit)

Breakage patterns discovered in audit
--------------------------------------
P1  innerHTML missing on container blocks         → warn, default to ''
P2  Duplicate blockIds (same-section copy-paste)  → warn, regenerate dupes
P3  Root block missing style/meta fields          → warn, patch with defaults
P4  Duplicate blockIds across repeated sections   → warn, regenerate dupes
P5  attributes field absent from non-leaf blocks  → default to {}
P6  blockId reuse inside deeply nested children   → regenerate, keep tree intact
"""

import json
import copy
import pytest
import sys
import os

sys.path.insert(0, os.path.dirname(__file__))
from validator import process, validate, fix_block, strip_fences

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def all_block_ids(blocks):
    ids = []
    for b in blocks:
        ids.append(b.get("blockId"))
        ids.extend(all_block_ids(b.get("children", [])))
    return ids

def find_block(blocks, block_id):
    for b in blocks:
        if b.get("blockId") == block_id:
            return b
        found = find_block(b.get("children", []), block_id)
        if found:
            return found
    return None

def minimal_page(extra_blocks=None):
    return {
        "page_title": "Test",
        "blocks": [
            {
                "blockId": "root",
                "element": "div",
                "originalElement": "body",
                "draggable": False,
                "children": extra_blocks or [],
                "baseStyles": {"display": "flex", "flexDirection": "column"},
                "mobileStyles": {}, "tabletStyles": {}, "rawStyles": {},
                "classes": [], "dataKey": None, "dynamicValues": [],
                "blockClientScript": "", "blockDataScript": "",
                "props": {}, "customAttributes": {}, "activeState": None
            }
        ]
    }

# ---------------------------------------------------------------------------
# BASELINE TESTS (original 12)
# ---------------------------------------------------------------------------

class TestStripFences:
    def test_strips_json_fence(self):
        assert strip_fences("```json\n{}\n```") == "{}"

    def test_strips_plain_fence(self):
        assert strip_fences("```\n{}\n```") == "{}"

    def test_passthrough_clean_json(self):
        assert strip_fences('{"a": 1}') == '{"a": 1}'

    def test_strips_leading_trailing_whitespace(self):
        assert strip_fences("  \n{}\n  ") == "{}"


class TestProcessBasic:
    def test_valid_json_returns_no_error(self):
        raw = json.dumps(minimal_page())
        _, _, err = process(raw)
        assert err is None

    def test_fenced_json_parsed(self):
        raw = "```json\n" + json.dumps(minimal_page()) + "\n```"
        result, _, err = process(raw)
        assert err is None
        assert result["page_title"] == "Test"

    def test_totally_invalid_returns_error(self):
        _, _, err = process("not json at all !!!")
        assert err is not None

    def test_partial_json_recovered(self):
        raw = 'prefix garbage {"page_title":"X","blocks":[{"blockId":"root","element":"div","children":[]}]} suffix'
        result, _, err = process(raw)
        assert err is None
        assert result["page_title"] == "X"


class TestValidateDefaults:
    def test_missing_page_title_defaults(self):
        data = {"blocks": [{"blockId": "root", "element": "div", "children": []}]}
        result, _ = validate(data)
        assert result["page_title"] == "Generated Page"

    def test_missing_blocks_field_warns(self):
        data = {"page_title": "X"}
        _, warnings = validate(data)
        assert any("missing blocks" in w for w in warnings)

    def test_empty_blocks_gets_root(self):
        data = {"page_title": "X", "blocks": []}
        result, _ = validate(data)
        assert result["blocks"][0]["blockId"] == "root"

    def test_blocks_as_string_parsed(self):
        inner = [{"blockId": "root", "element": "div", "children": []}]
        data = {"page_title": "X", "blocks": json.dumps(inner)}
        result, _ = validate(data)
        assert isinstance(result["blocks"], list)
        assert result["blocks"][0]["blockId"] == "root"


class TestRootWrapping:
    def test_non_root_first_block_gets_wrapped(self):
        data = {
            "page_title": "X",
            "blocks": [{"blockId": "hero1", "element": "section", "children": []}]
        }
        result, warnings = validate(data)
        assert result["blocks"][0]["blockId"] == "root"
        assert any("wrapping" in w for w in warnings)

    def test_wrapped_root_contains_original_as_child(self):
        data = {
            "page_title": "X",
            "blocks": [{"blockId": "hero1", "element": "section", "children": []}]
        }
        result, _ = validate(data)
        child_ids = [c["blockId"] for c in result["blocks"][0]["children"]]
        assert "hero1" in child_ids


class TestDuplicateBlockIds:
    def test_duplicate_ids_regenerated(self):
        """Baseline: two blocks share the same blockId."""
        data = {
            "page_title": "X",
            "blocks": [
                {
                    "blockId": "root",
                    "element": "div",
                    "children": [
                        {"blockId": "dup001", "element": "div", "children": []},
                        {"blockId": "dup001", "element": "p", "children": []},
                    ]
                }
            ]
        }
        result, warnings = validate(data)
        ids = all_block_ids(result["blocks"])
        assert len(ids) == len(set(ids)), "IDs must be unique after validation"
        assert any("dup001" in w for w in warnings)


# ---------------------------------------------------------------------------
# NEW TESTS — patterns discovered from Person B's files
# ---------------------------------------------------------------------------

class TestMissingInnerHTML:
    """P1 — innerHTML absent on container / structural blocks."""

    def test_missing_innerHTML_on_section_gets_default(self):
        """agency_consulting / coffee_shop pattern: container block has no innerHTML."""
        data = {
            "page_title": "Test",
            "blocks": [
                {
                    "blockId": "root",
                    "element": "div",
                    "children": [
                        {
                            "blockId": "sec001",
                            "element": "section",
                            # innerHTML intentionally absent
                            "children": [],
                            "baseStyles": {}
                        }
                    ]
                }
            ]
        }
        result, warnings = validate(data)
        sec = find_block(result["blocks"], "sec001")
        assert sec["innerHTML"] == ""
        assert any("sec001" in w and "innerHTML" in w for w in warnings)

    def test_missing_innerHTML_on_root_gets_default(self):
        """Root block itself also had no innerHTML in every Person B file."""
        data = {
            "page_title": "Test",
            "blocks": [
                {
                    "blockId": "root",
                    "element": "div",
                    "children": [],
                    # no innerHTML
                    "baseStyles": {"display": "flex"}
                }
            ]
        }
        result, warnings = validate(data)
        root = result["blocks"][0]
        assert "innerHTML" in root
        assert root["innerHTML"] == ""

    def test_present_innerHTML_untouched(self):
        """If innerHTML is present, it must not be overwritten."""
        data = minimal_page([
            {"blockId": "h1a", "element": "h1", "children": [],
             "innerHTML": "<p>Hello</p>", "baseStyles": {}}
        ])
        result, _ = validate(data)
        h1 = find_block(result["blocks"], "h1a")
        assert h1["innerHTML"] == "<p>Hello</p>"


class TestDuplicateBlockIdsSameSection:
    """P2 — modern_restaurant.json had 'poiuytrewq' used in both menu columns."""

    def test_same_id_in_sibling_columns_both_get_unique_ids(self):
        data = {
            "page_title": "Restaurant",
            "blocks": [
                {
                    "blockId": "root",
                    "element": "div",
                    "children": [
                        {
                            "blockId": "col1",
                            "element": "div",
                            "children": [
                                {"blockId": "poiuytrewq", "element": "p",
                                 "children": [], "innerHTML": "col 1 text"}
                            ]
                        },
                        {
                            "blockId": "col2",
                            "element": "div",
                            "children": [
                                {"blockId": "poiuytrewq", "element": "p",
                                 "children": [], "innerHTML": "col 2 text"}
                            ]
                        }
                    ]
                }
            ]
        }
        result, warnings = validate(data)
        ids = all_block_ids(result["blocks"])
        assert len(ids) == len(set(ids))
        assert any("poiuytrewq" in w for w in warnings)

    def test_innerHTML_preserved_after_id_regen(self):
        """After regeneration both paragraphs should keep their original text."""
        data = {
            "page_title": "Restaurant",
            "blocks": [
                {
                    "blockId": "root",
                    "element": "div",
                    "children": [
                        {"blockId": "poiuytrewq", "element": "p",
                         "children": [], "innerHTML": "specials text"},
                        {"blockId": "poiuytrewq", "element": "p",
                         "children": [], "innerHTML": "menu text"}
                    ]
                }
            ]
        }
        result, _ = validate(data)
        texts = [b["innerHTML"] for b in result["blocks"][0]["children"]]
        assert "specials text" in texts
        assert "menu text" in texts


class TestRootMissingStyleFields:
    """P3 — pricing_page.json root block had only blockId/element/originalElement/draggable/children."""

    def test_root_without_baseStyles_gets_defaults(self):
        data = {
            "page_title": "Pricing",
            "blocks": [
                {
                    "blockId": "root",
                    "element": "div",
                    "originalElement": "body",
                    "draggable": False,
                    "children": []
                    # baseStyles, mobileStyles, tabletStyles, rawStyles, classes, etc. absent
                }
            ]
        }
        result, warnings = validate(data)
        root = result["blocks"][0]
        assert isinstance(root["baseStyles"], dict)
        assert root["baseStyles"].get("display") == "flex"
        assert isinstance(root.get("mobileStyles"), dict)
        assert isinstance(root.get("classes"), list)
        assert any("root block" in w for w in warnings)

    def test_root_with_existing_baseStyles_not_overwritten(self):
        data = {
            "page_title": "X",
            "blocks": [
                {
                    "blockId": "root",
                    "element": "div",
                    "children": [],
                    "baseStyles": {"backgroundColor": "#000"},
                    "mobileStyles": {}, "tabletStyles": {}, "rawStyles": {},
                    "classes": []
                }
            ]
        }
        result, _ = validate(data)
        assert result["blocks"][0]["baseStyles"] == {"backgroundColor": "#000"}


class TestDuplicateIdsAcrossRepeatedSections:
    """P4 — saas_landing.json reused 'td7flekhp', 'f1q2sdfgh', 'g4hjklmn', 'p1q2sdfgh'
       across features-grid and footer sections."""

    def test_four_duplicate_ids_all_become_unique(self):
        shared_child = lambda text: {
            "blockId": "g4hjklmn", "element": "h2",
            "children": [], "innerHTML": text
        }
        shared_section = lambda bid, text: {
            "blockId": bid, "element": "section",
            "children": [
                {"blockId": "f1q2sdfgh", "element": "div",
                 "children": [shared_child(text)]}
            ]
        }
        data = {
            "page_title": "SaaS",
            "blocks": [
                {
                    "blockId": "root",
                    "element": "div",
                    "children": [
                        shared_section("td7flekhp", "Features"),
                        shared_section("td7flekhp", "Footer"),
                    ]
                }
            ]
        }
        result, warnings = validate(data)
        ids = all_block_ids(result["blocks"])
        assert len(ids) == len(set(ids))
        # At least one duplicate warned about
        assert any("td7flekhp" in w or "f1q2sdfgh" in w or "g4hjklmn" in w
                   for w in warnings)


class TestWrongTypeFields:
    """P5 — attributes / baseStyles / classes arriving as wrong types."""

    def test_baseStyles_as_string_reset_to_dict(self):
        data = minimal_page([
            {"blockId": "blk1", "element": "div", "children": [],
             "baseStyles": "display:flex"}   # invalid: should be dict
        ])
        result, warnings = validate(data)
        blk = find_block(result["blocks"], "blk1")
        assert isinstance(blk["baseStyles"], dict)
        assert any("baseStyles" in w for w in warnings)

    def test_classes_as_string_reset_to_list(self):
        data = minimal_page([
            {"blockId": "blk2", "element": "div", "children": [],
             "classes": "hero-class"}   # invalid: should be list
        ])
        result, warnings = validate(data)
        blk = find_block(result["blocks"], "blk2")
        assert isinstance(blk["classes"], list)
        assert any("classes" in w for w in warnings)

    def test_dynamicValues_as_null_reset_to_list(self):
        data = minimal_page([
            {"blockId": "blk3", "element": "div", "children": [],
             "dynamicValues": None}
        ])
        result, warnings = validate(data)
        blk = find_block(result["blocks"], "blk3")
        assert isinstance(blk["dynamicValues"], list)

    def test_children_as_string_reset_to_list(self):
        data = minimal_page([
            {"blockId": "blk4", "element": "div",
             "children": "not-a-list"}
        ])
        result, warnings = validate(data)
        blk = find_block(result["blocks"], "blk4")
        assert isinstance(blk["children"], list)
        assert any("children" in w for w in warnings)


class TestDeeplyNestedDuplicates:
    """P6 — duplicate IDs buried in deeply nested children (developer_portfolio pattern)."""

    def test_deep_duplicate_regenerated(self):
        data = {
            "page_title": "Portfolio",
            "blocks": [
                {
                    "blockId": "root",
                    "element": "div",
                    "children": [
                        {
                            "blockId": "skills",
                            "element": "section",
                            "children": [
                                {
                                    "blockId": "col_a",
                                    "element": "div",
                                    "children": [
                                        {"blockId": "shared_id", "element": "h2",
                                         "children": [], "innerHTML": "Front-end"}
                                    ]
                                },
                                {
                                    "blockId": "col_b",
                                    "element": "div",
                                    "children": [
                                        {"blockId": "shared_id", "element": "h2",
                                         "children": [], "innerHTML": "Back-end"}
                                    ]
                                }
                            ]
                        }
                    ]
                }
            ]
        }
        result, warnings = validate(data)
        ids = all_block_ids(result["blocks"])
        assert len(ids) == len(set(ids))
        # Both headings still present
        all_inner = []
        def collect_inner(blocks):
            for b in blocks:
                all_inner.append(b.get("innerHTML", ""))
                collect_inner(b.get("children", []))
        collect_inner(result["blocks"])
        assert "Front-end" in all_inner
        assert "Back-end" in all_inner


class TestRealFileRoundtrip:
    """Run each of Person B's actual files through process() and verify invariants."""

    FILES = [
        "agency_consulting.json",
        "coffee_shop.json",
        "developer_portfolio.json",
        "ecommerce_product.json",
        "event_webinar.json",
        "mobile_app_promo.json",
        "modern_restaurant.json",
        "pricing_page.json",
        "saas_landing.json",
    ]

    @pytest.mark.parametrize("fname", FILES)
    def test_no_error(self, fname):
        path = os.path.join(os.path.dirname(__file__), fname)
        if not os.path.exists(path):
            pytest.skip(f"{fname} not found")
        with open(path) as f:
            raw = f.read()
        _, _, err = process(raw)
        assert err is None, f"{fname} returned error: {err}"

    @pytest.mark.parametrize("fname", FILES)
    def test_unique_block_ids(self, fname):
        path = os.path.join(os.path.dirname(__file__), fname)
        if not os.path.exists(path):
            pytest.skip(f"{fname} not found")
        with open(path) as f:
            raw = f.read()
        result, _, _ = process(raw)
        ids = all_block_ids(result["blocks"])
        dupes = [x for x in ids if ids.count(x) > 1]
        assert not dupes, f"{fname} still has duplicate IDs after validation: {set(dupes)}"

    @pytest.mark.parametrize("fname", FILES)
    def test_first_block_is_root(self, fname):
        path = os.path.join(os.path.dirname(__file__), fname)
        if not os.path.exists(path):
            pytest.skip(f"{fname} not found")
        with open(path) as f:
            raw = f.read()
        result, _, _ = process(raw)
        assert result["blocks"][0]["blockId"] == "root"

    @pytest.mark.parametrize("fname", FILES)
    def test_all_blocks_have_required_fields(self, fname):
        path = os.path.join(os.path.dirname(__file__), fname)
        if not os.path.exists(path):
            pytest.skip(f"{fname} not found")
        with open(path) as f:
            raw = f.read()
        result, _, _ = process(raw)
        required = ['blockId', 'element', 'children', 'innerHTML',
                    'baseStyles', 'mobileStyles', 'tabletStyles', 'rawStyles',
                    'classes', 'dataKey', 'dynamicValues',
                    'blockClientScript', 'blockDataScript',
                    'props', 'customAttributes', 'activeState']
        missing = []
        def check(blocks):
            for b in blocks:
                for r in required:
                    if r not in b:
                        missing.append(f"{b.get('blockId', '?')}.{r}")
                check(b.get("children", []))
        check(result["blocks"])
        assert not missing, f"{fname} blocks still missing fields: {missing[:5]}"