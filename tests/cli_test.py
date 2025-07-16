"""Test the CLI."""

import pytest
from click.testing import CliRunner

from sasquatchbackpack.sources.usgs import commands as usgs


@pytest.mark.parametrize(
    (
        "duration",
        "radius",
        "coords",
        "magnitude_bounds",
        "publish_mode",
        "expected",
    ),
    [
        (
            (50, 0),
            400,
            (-30.22573200864174, -70.73932987127506),
            (2, 10),
            "NONE",
            ["SUCCESS"],
        ),  # Common usage
        (
            (10001, 0),
            400,
            (-30.22573200864174, -70.73932987127506),
            (2, 10),
            "NONE",
            ["duration", "large"],
        ),
        (
            (0, 0),
            400,
            (-30.22573200864174, -70.73932987127506),
            (2, 10),
            "NONE",
            ["duration", "small"],
        ),
        (
            (50, 0),
            5001,
            (-30.22573200864174, -70.73932987127506),
            (2, 10),
            "NONE",
            ["radius", "large"],
        ),
        (
            (50, 0),
            0,
            (-30.22573200864174, -70.73932987127506),
            (2, 10),
            "NONE",
            ["radius", "small"],
        ),
        (
            (50, 0),
            400,
            (-91, -70.73932987127506),
            (2, 10),
            "NONE",
            ["latitude", "out of bounds"],
        ),
        (
            (50, 0),
            400,
            (91, -70.73932987127506),
            (2, 10),
            "NONE",
            ["latitude", "out of bounds"],
        ),
        (
            (50, 0),
            400,
            (-30.22573200864174, -181),
            (2, 10),
            "NONE",
            ["longitude", "out of bounds"],
        ),
        (
            (50, 0),
            400,
            (-30.22573200864174, 181),
            (2, 10),
            "NONE",
            ["longitude", "out of bounds"],
        ),
        (
            (50, 0),
            100,
            (-30.22573200864174, -70.73932987127506),
            (-1, 10),
            "NONE",
            ["minimum magnitude", "out of bounds"],
        ),
        (
            (50, 0),
            100,
            (-30.22573200864174, -70.73932987127506),
            (11, 10),
            "NONE",
            ["minimum magnitude", "out of bounds"],
        ),
        (
            (50, 0),
            100,
            (-30.22573200864174, -70.73932987127506),
            (2, -1),
            "NONE",
            ["maximum magnitude", "out of bounds"],
        ),
        (
            (50, 0),
            100,
            (-30.22573200864174, -70.73932987127506),
            (2, 11),
            "NONE",
            ["maximum magnitude", "out of bounds"],
        ),
        (
            (50, 0),
            100,
            (-30.22573200864174, -70.73932987127506),
            (10, 2),
            "NONE",
            [
                "minimum magnitude",
                "cannot excede",
                "maximum magnitude",
            ],
        ),
        (
            (50, 0),
            100,
            (-30.22573200864174, -70.73932987127506),
            (2, 10),
            "INVALID",
            [
                "did not match",
                "publish method",
            ],
        ),
    ],
)
def test_usgs_earthquake_data(
    duration: tuple[int, int],
    radius: int,
    coords: tuple[float, float],
    magnitude_bounds: tuple[int, int],
    publish_mode: str,
    expected: list[str],
) -> None:
    """Ensure fringe user input functions as intended."""
    runner = CliRunner()

    result = runner.invoke(
        usgs.usgs_earthquake_data,
        [
            "-d",
            str(duration[0]),
            str(duration[1]),
            "-r",
            str(radius),
            "-c",
            str(coords[0]),
            str(coords[1]),
            "-m",
            str(magnitude_bounds[0]),
            str(magnitude_bounds[1]),
            "-pm",
            publish_mode,
        ],
        input="N",
    )

    for value in expected:
        assert value in result.output
