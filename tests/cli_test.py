"""Test the CLI"""

import pytest
from click.testing import CliRunner

from sasquatchbackpack import cli


@pytest.mark.parametrize(
    "duration, radius, coords, magnitude_bounds, expected",
    [
        (
            (50, 0),
            400,
            (-30.22573200864174, -70.73932987127506),
            (2, 10),
            ["SUCCESS"],
        ),  # Common usage
        (
            (10001, 0),
            400,
            (-30.22573200864174, -70.73932987127506),
            (2, 10),
            ["duration", "too large"],
        ),
        (
            (0, 0),
            400,
            (-30.22573200864174, -70.73932987127506),
            (2, 10),
            ["duration", "too small"],
        ),
        (
            (50, 0),
            5001,
            (-30.22573200864174, -70.73932987127506),
            (2, 10),
            ["radius", "too large"],
        ),
        (
            (50, 0),
            0,
            (-30.22573200864174, -70.73932987127506),
            (2, 10),
            ["radius", "too small"],
        ),
        (
            (50, 0),
            400,
            (-91, -70.73932987127506),
            (2, 10),
            ["latitude", "too low"],
        ),
        (
            (50, 0),
            400,
            (91, -70.73932987127506),
            (2, 10),
            ["latitude", "too high"],
        ),
        (
            (50, 0),
            400,
            (-30.22573200864174, -181),
            (2, 10),
            ["longitude", "too low"],
        ),
        (
            (50, 0),
            400,
            (-30.22573200864174, 181),
            (2, 10),
            ["longitude", "too high"],
        ),
        (
            (50, 0),
            400,
            (-30.22573200864174, -181),
            (2, 10),
            ["longitude", "too low"],
        ),
        (
            (50, 0),
            400,
            (-30.22573200864174, 181),
            (2, 10),
            ["longitude", "too high"],
        ),
        (
            (50, 0),
            100,
            (-30.22573200864174, -70.73932987127506),
            (-1, 10),
            ["minimum magnitude", "too small"],
        ),
        (
            (50, 0),
            100,
            (-30.22573200864174, -70.73932987127506),
            (11, 10),
            ["minimum magnitude", "too large"],
        ),
        (
            (50, 0),
            100,
            (-30.22573200864174, -70.73932987127506),
            (2, -1),
            ["maximum magnitude", "too small"],
        ),
        (
            (50, 0),
            100,
            (-30.22573200864174, -70.73932987127506),
            (2, 11),
            ["maximum magnitude", "too large"],
        ),
        (
            (50, 0),
            100,
            (-30.22573200864174, -70.73932987127506),
            (10, 2),
            [
                "minimum magnitude",
                "cannot excede",
                "maximum magnitude",
            ],
        ),
    ],
)
def test_usgs_earthquake_data(
    duration: tuple[int, int],
    radius: int,
    coords: tuple[float, float],
    magnitude_bounds: tuple[int, int],
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
            "-m",
            str(magnitude_bounds[0]),
            str(magnitude_bounds[1]),
        ],
    )

    if "SUCCESS" in expected:
        assert result.exit_code == 0

    for value in expected:
        assert value in result.output
