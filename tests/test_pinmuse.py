import json
from pathlib import Path

import pytest
from PIL import Image

from pinmuse import aesthetics, analyze, formats, prompt
from pinmuse.compose import TEMPLATES, Design, render
from pinmuse.models import Pin
from pinmuse.pinterest import web
from pinmuse.providers import GenRequest, pick
from pinmuse.providers.procedural import STYLES, ProceduralProvider

FIX = Path(__file__).parent / "fixtures"


@pytest.fixture
def images(tmp_path):
    paths = []
    for i, c in enumerate(["#2B2118", "#7A5C3E", "#B59368", "#E6D5B8"]):
        p = tmp_path / f"img{i}.jpg"
        Image.new("RGB", (200, 300), c).save(p)
        paths.append(str(p))
    return paths


def test_search_parses_pins_and_skips_ads(monkeypatch):
    payload = json.loads((FIX / "search_response.json").read_text())
    monkeypatch.setattr(web.http, "get_json", lambda *a, **k: payload)
    pins = web.search("dark academia", limit=10)
    assert [p.id for p in pins] == ["1111", "2222"]
    assert pins[0].image_url.endswith("/originals/aa/bb/cc/1111.jpg")  # largest variant
    assert pins[0].saves == 4200 and pins[0].board == "Dark Academia"
    assert pins[0].url == "https://www.pinterest.com/pin/1111/"


def test_upgrade_pinimg():
    assert web.upgrade_pinimg("https://i.pinimg.com/236x/a/b.jpg") == "https://i.pinimg.com/736x/a/b.jpg"


def test_moodboard(images, tmp_path):
    pins = [Pin(id=str(i), image_url="x", local_path=p, width=200, height=300,
                description="dark academia library books candle autumn") for i, p in enumerate(images)]
    mb = analyze.build_moodboard("dark academia", pins, tmp_path)
    assert len(mb.palette) >= 3 and mb.palette[0].startswith("#")
    assert mb.aesthetic == "dark-academia"
    assert mb.orientation == "portrait"
    assert Path(mb.contact_sheet).exists()


def test_prompt_mentions_palette_and_space(images, tmp_path):
    pins = [Pin(id="1", image_url="x", local_path=images[0], description="cozy library")]
    mb = analyze.build_moodboard("library", pins)
    p = prompt.build("a reading nook", mb, fmt=formats.get("story"), template="story")
    assert "reading nook" in p["prompt"] and mb.palette[0] in p["prompt"] and "9:16" in p["prompt"]


@pytest.mark.parametrize("style", sorted(STYLES))
def test_procedural_styles(tmp_path, style):
    out = ProceduralProvider().generate(GenRequest("test", tmp_path / "a.png", width=300, height=450,
                                                   palette=list(aesthetics.get("y2k").palette)), style=style)
    assert Image.open(out).size == (300, 450)


@pytest.mark.parametrize("template", sorted(TEMPLATES))
def test_every_template_renders(template, images, tmp_path):
    f = formats.get("ig-post")
    ds = Design(template=template, fmt=f, images=images, title="Slow Living", subtitle="Quiet mornings",
                kicker="Vol 1", handle="@me", cta="Save", body="one\ntwo",
                slides=[{"title": "Tip", "body": "Do the thing."}])
    outs = render(ds, tmp_path / "x.jpg")
    assert outs and all(Image.open(o).size == (f.width, f.height) for o in outs)
    if template == "carousel":
        assert len(outs) == 3


def test_auto_provider_falls_back_to_procedural(monkeypatch):
    for k in ["OPENAI_API_KEY", "GEMINI_API_KEY", "GOOGLE_API_KEY", "FAL_KEY", "REPLICATE_API_TOKEN",
              "TOGETHER_API_KEY", "STABILITY_API_KEY", "PINMUSE_IMAGE_CMD", "PINMUSE_PROVIDER"]:
        monkeypatch.delenv(k, raising=False)
    monkeypatch.setattr("pinmuse.providers.local._up", lambda *a, **k: False)
    assert pick("auto").name == "procedural"


def test_formats_custom_and_alias():
    assert formats.get("story").height == 1920
    assert (formats.get("800x1200").width, formats.get("800x1200").height) == (800, 1200)


def test_create_end_to_end_local_inspo(images, tmp_path):
    from pinmuse.pipeline import create
    m = create("reading nook", inspo=str(Path(images[0]).parent), template="story", fmt="ig-story",
               title="Study Season", provider="procedural", out_dir=str(tmp_path), seed=1)
    assert Path(m["outputs"][0]).exists() and Path(m["caption"]).exists()
    assert m["hashtags"] and m["moodboard"]
