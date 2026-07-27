import pytest

from bookkit.diagrams import (
    MIN_FILL_CONTRAST,
    contrast_ratio,
    parse_color,
    relative_luminance,
)

BLACK = (0, 0, 0)
WHITE = (255, 255, 255)

# The interior's own tokens, as defined in assets/interior.css.
INK = (0x24, 0x24, 0x24)
PAPER = (0xFF, 0xFF, 0xFF)
ACCENT = (0xD5, 0x4B, 0x20)
SUPPORT = (0x17, 0x7C, 0x83)
CAUTION = (0x9A, 0x5A, 0x12)
MUTED = (0x68, 0x68, 0x68)


def test_luminance_of_black_is_zero():
    assert relative_luminance(BLACK) == pytest.approx(0.0)


def test_luminance_of_white_is_one():
    assert relative_luminance(WHITE) == pytest.approx(1.0)


def test_luminance_of_mid_grey_matches_wcag():
    assert relative_luminance((0x80, 0x80, 0x80)) == pytest.approx(0.2159, abs=1e-4)


def test_contrast_of_black_on_white_is_twenty_one():
    assert contrast_ratio(BLACK, WHITE) == pytest.approx(21.0, abs=1e-2)


def test_contrast_is_symmetric():
    assert contrast_ratio(ACCENT, SUPPORT) == pytest.approx(contrast_ratio(SUPPORT, ACCENT))


def test_contrast_of_a_colour_with_itself_is_one():
    assert contrast_ratio(ACCENT, ACCENT) == pytest.approx(1.0)


def test_ink_on_paper_is_strong():
    assert contrast_ratio(INK, PAPER) == pytest.approx(15.52, abs=0.05)


def test_accent_and_support_collapse_in_grayscale():
    """The motivating case. Obviously different in colour, the same grey in print."""
    assert contrast_ratio(ACCENT, SUPPORT) == pytest.approx(1.14, abs=0.02)
    assert contrast_ratio(ACCENT, SUPPORT) < MIN_FILL_CONTRAST


def test_every_mid_tone_pair_collapses():
    """The palette offers three tonal levels, not seven colours."""
    mid_tones = [ACCENT, SUPPORT, CAUTION, MUTED]

    for i, a in enumerate(mid_tones):
        for b in mid_tones[i + 1 :]:
            assert contrast_ratio(a, b) < MIN_FILL_CONTRAST


def test_mid_tones_are_distinguishable_from_ink_and_paper():
    for mid in (ACCENT, SUPPORT, CAUTION, MUTED):
        assert contrast_ratio(mid, INK) >= MIN_FILL_CONTRAST
        assert contrast_ratio(mid, PAPER) >= MIN_FILL_CONTRAST


def test_parse_color_reads_the_browser_rgb_form():
    assert parse_color("rgb(213, 75, 32)") == ACCENT


def test_parse_color_reads_rgba_with_alpha():
    assert parse_color("rgba(213, 75, 32, 0.5)") == ACCENT


def test_parse_color_reads_hex():
    assert parse_color("#d54b20") == ACCENT
    assert parse_color("#FFF") == WHITE


def test_parse_color_returns_none_for_absent_paint():
    assert parse_color("none") is None
    assert parse_color("transparent") is None
    assert parse_color("rgba(0, 0, 0, 0)") is None
    assert parse_color("") is None
