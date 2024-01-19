from datetime import timedelta

import click

from sasquatchbackpack.scripts import usgs


@click.group(context_settings={"help_option_names": ["-h", "--help"]})
@click.version_option(message="%(version)s")
def main() -> None:
    """Administrative command-line interface for sasquatchbackpack."""


@main.command()
@click.option(
    "-d",
    "--duration",
    help="How far back from the present should be searched in days, \
        then hours.",
    required=True,
    type=(int, int),
)
@click.option(
    "-r",
    "--radius",
    help="radius of search from central coordinates in km.",
    default=400,
    type=int,
    show_default=True,
)
@click.option(
    "-c",
    "--coords",
    help="latitude and longitude of the central coordnates. Latitude \
        is first and Longitude is second. Defaults to the coordinates \
            of Cerro Pachon.",
    default=(-30.22573200864174, -70.73932987127506),
    type=(float, float),
    show_default=True,
)
@click.option(
    "-mm",
    "--min-magnitude",
    help="minimum earthquake magnitude.",
    default=2,
    type=int,
    show_default=True,
)
@click.option(
    "-xm",
    "--max-magnitude",
    help="maximum earthquake magnitude.",
    default=10,
    type=int,
    show_default=True,
)
def search_usgs(
    duration: tuple[int, int],
    radius: int,
    coords: tuple[float, float],
    min_magnitude: int,
    max_magnitude: int,
) -> None:
    """Seaches USGS databases for relevant earthquake data and prints it
    to console
    """
    results = usgs.search_api(
        timedelta(duration[0], 0, 0, 0, 0, duration[1], 0),
        radius,
        coords,
        min_magnitude,
        max_magnitude,
    )
    for result in results:
        print(result)
