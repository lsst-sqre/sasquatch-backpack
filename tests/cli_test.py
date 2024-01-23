"""Test the CLI"""

import pytest
from click.testing import CliRunner

from sasquatchbackpack import cli


@pytest.mark.parametrize(
    "duration, radius, coords, min_magnitude, max_magnitude, expected",
    [
        (
            (50, 0),
            400,
            (-30.22573200864174, -70.73932987127506),
            2,
            10,
            ["SUCCESS"],
        ),  # Common usage
        (
            (10001, 0),
            400,
            (-30.22573200864174, -70.73932987127506),
            2,
            10,
            ["FAILURE", "duration", "too large"],
        ),
        (
            (0, 0),
            400,
            (-30.22573200864174, -70.73932987127506),
            2,
            10,
            ["FAILURE", "duration", "too small"],
        ),
        (
            (50, 0),
            5001,
            (-30.22573200864174, -70.73932987127506),
            2,
            10,
            ["FAILURE", "radius", "too large"],
        ),
        (
            (50, 0),
            0,
            (-30.22573200864174, -70.73932987127506),
            2,
            10,
            ["FAILURE", "radius", "too small"],
        ),
        (
            (50, 0),
            400,
            (-91, -70.73932987127506),
            2,
            10,
            ["FAILURE", "latitude", "too low"],
        ),
        (
            (50, 0),
            400,
            (91, -70.73932987127506),
            2,
            10,
            ["FAILURE", "latitude", "too high"],
        ),
        (
            (50, 0),
            400,
            (-30.22573200864174, -181),
            2,
            10,
            ["FAILURE", "longitude", "too low"],
        ),
        (
            (50, 0),
            400,
            (-30.22573200864174, 181),
            2,
            10,
            ["FAILURE", "longitude", "too high"],
        ),
        (
            (50, 0),
            400,
            (-30.22573200864174, -181),
            2,
            10,
            ["FAILURE", "longitude", "too low"],
        ),
        (
            (50, 0),
            400,
            (-30.22573200864174, 181),
            2,
            10,
            ["FAILURE", "longitude", "too high"],
        ),
        (
            (50, 0),
            100,
            (-30.22573200864174, -70.73932987127506),
            -1,
            10,
            ["FAILURE", "minimum magnitude", "too small"],
        ),
        (
            (50, 0),
            100,
            (-30.22573200864174, -70.73932987127506),
            11,
            10,
            ["FAILURE", "minimum magnitude", "too large"],
        ),
        (
            (50, 0),
            100,
            (-30.22573200864174, -70.73932987127506),
            2,
            -1,
            ["FAILURE", "maximum magnitude", "too small"],
        ),
        (
            (50, 0),
            100,
            (-30.22573200864174, -70.73932987127506),
            2,
            11,
            ["FAILURE", "maximum magnitude", "too large"],
        ),
        (
            (50, 0),
            100,
            (-30.22573200864174, -70.73932987127506),
            10,
            2,
            [
                "FAILURE",
                "minimum magnitude",
                "cannot excede",
                "maximum magnitude",
            ],
        ),
        (
            (10001, 0),
            0,
            (-30.22573200864174, -70.73932987127506),
            2,
            10,
            [
                "FAILURE",
                "duration",
                "too large",
                "radius",
                "too small",
            ],
        ),
        (
            (50, 0),
            400,
            (91, -181),
            2,
            10,
            [
                "FAILURE",
                "longitude",
                "too high",
                "latitude",
                "too low",
            ],
        ),
        (
            (50, 0),
            400,
            (-30.22573200864174, -70.73932987127506),
            11,
            -1,
            [
                "FAILURE",
                "minimum magnitude",
                "too large",
                "maximum magnitude",
                "too small",
                "cannot excede",
            ],
        ),
        (
            (10001, 0),
            0,
            (-91, 181),
            11,
            -1,
            [
                "FAILURE",
                "duration",
                "too large",
                "radius",
                "too small",
                "latitude",
                "too low",
                "longitude",
                "too high",
                "minimum magnitude",
                "maximum magnitude",
                "cannot excede",
            ],
        ),
    ],
)
def test_usgs_earthquake_data(
    duration: tuple[int, int],
    radius: int,
    coords: tuple[float, float],
    min_magnitude: int,
    max_magnitude: int,
    expected: list[str],
) -> None:
    """Ensure fringe user input functions as intended"""
    runner = CliRunner()

    result = runner.invoke(
        cli.usgs_earthquake_data,
        [
            "-d",
            str(duration[0]),
            str(duration[1]),
            "-r",
            str(radius),
            "-c",
            str(coords[0]),
            str(coords[1]),
            "-mm",
            str(min_magnitude),
            "-xm",
            str(max_magnitude),
        ],
    )

    if "SUCCESS" in expected:
        assert result.exit_code == 0

    for value in expected:
        assert value in result.output
