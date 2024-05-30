from datetime import timedelta

import click

from sasquatchbackpack import sasquatch, sources
from sasquatchbackpack.scripts import usgs

DEFAULT_RADIUS = 400

DEFAULT_COORDS = (-30.22573200864174, -70.73932987127506)

DEFAULT_MAGNITUDE_BOUNDS = (2, 10)

DEFAULT_TEST = False


def check_duration(
    ctx: click.Context, param: dict, value: tuple[int, int]
) -> tuple[int, int]:
    """Validate duration inputs"""
    total_duration = timedelta(value[0], 0, 0, 0, 0, value[1], 0)

    if total_duration > timedelta(10000, 0, 0, 0, 0, 0, 0):
        raise click.BadParameter(
            f"""Your provided duration ({str(total_duration)}) is
    too large. The maximum is 10000 days."""
        )
    elif total_duration < timedelta(0, 0, 0, 0, 0, 1, 0):
        raise click.BadParameter(
            f"""Your provided duration ({str(total_duration)}) is
    too small. The minimum is 1 hour."""
        )

    return value


def check_radius(ctx: click.Context, param: dict, value: int) -> int:
    """Validate radius inputs"""
    if value > 5000:
        raise click.BadParameter(
            f"""Your provided radius ({value}) is too large.
 The maximum is 5000."""
        )
    elif value <= 0:
        raise click.BadParameter(
            f"""Your provided radius ({value}) is too small.
 The minimum is 0.1."""
        )

    return value


def check_coords(
    ctx: click.Context, param: dict, value: tuple[float, float]
) -> tuple[float, float]:
    """Validate coords inputs"""
    if value[0] < -90.0:
        raise click.BadParameter(
            f"""Your provided latitude ({value[0]}) is too low.
 The minimum is -90."""
        )
    elif value[0] > 90.0:
        raise click.BadParameter(
            f"""Your provided latitude ({value[0]}) is too high.
 The maximum is 90."""
        )

    if value[1] < -180:
        raise click.BadParameter(
            f"""Your provided longitude ({value[1]}) is too low.
 The minimum is -180."""
        )
    elif value[1] > 180:
        raise click.BadParameter(
            f"""Your provided longitude ({value[1]}) is too high.
 The maximum is 180."""
        )

    return value


def check_magnitude_bounds(
    ctx: click.Context, param: dict, value: tuple[int, int]
) -> tuple[int, int]:
    """Validate magnitude bounds"""
    if value[0] < 0:
        raise click.BadParameter(
            f"""Your provided minimum magnitude ({value[0]}) is
 too small. The minimum is 0."""
        )
    elif value[0] > 10:
        raise click.BadParameter(
            f"""Your provided minimum magnitude ({value[0]}) is
 too large. The maximum is 10."""
        )

    if value[1] > 10:
        raise click.BadParameter(
            f"""Your provided maximum magnitude ({value[1]}) is
 too large. The maximum is 10."""
        )
    elif value[1] < 0:
        raise click.BadParameter(
            f"""Your provided maximum magnitude ({value[1]}) is
 too small. The minimum is 0."""
        )

    if value[0] > value[1]:
        raise click.BadParameter(
            f"""Your provided minimum magnitude ({value[0]})
cannot excede your provided maximum magnitude ({value[1]})."""
        )

    return value


@click.group(context_settings={"help_option_names": ["-h", "--help"]})
@click.version_option(message="%(version)s")
def main() -> None:
    """Command-line interface for sasquatchbackpack."""


@main.command()
@click.option(
    "-d",
    "--duration",
    help="How far back from the present should be searched" + " (days, hours)",
    required=True,
    type=(int, int),
    callback=check_duration,
)
@click.option(
    "-r",
    "--radius",
    help="radius of search from central coordinates in km.",
    default=DEFAULT_RADIUS,
    type=int,
    show_default=True,
    callback=check_radius,
)
@click.option(
    "-c",
    "--coords",
    help="latitude and longitude of the central coordnates"
    + " (latitude, longitude). Defaults to the coordinates of"
    + " Cerro Pachon.",
    default=DEFAULT_COORDS,
    type=(float, float),
    show_default=True,
    callback=check_coords,
)
@click.option(
    "-m",
    "--magnitude-bounds",
    help="upper and lower bounds (lower, upper)",
    default=DEFAULT_MAGNITUDE_BOUNDS,
    type=(int, int),
    show_default=True,
    callback=check_magnitude_bounds,
)
@click.option(
    "-t",
    "--test",
    help="set to True to echo API results without sending them",
    default=DEFAULT_TEST,
    type=bool,
    show_default=True,
)
def usgs_earthquake_data(
    duration: tuple[int, int],
    radius: int,
    coords: tuple[float, float],
    magnitude_bounds: tuple[int, int],
    test: bool,
) -> None:
    """Seaches USGS databases for relevant earthquake data and prints it
    to console
    """
    total_duration = timedelta(duration[0], 0, 0, 0, 0, duration[1], 0)

    results = usgs.search_api(
        total_duration,
        radius,
        coords,
        magnitude_bounds,
    )

    if len(results) > 0:
        click.secho("SUCCESS!", fg="green")
        click.echo("------")
        for result in results:
            click.echo(result)
        click.echo("------")
    else:
        click.secho("SUCCESS! (kinda)", fg="yellow")
        click.echo("------")
        click.echo("No results found for the provided criteria :(")
        click.echo("------")
        return

    if not test:
        click.echo("Sending data...")

        config = sources.USGSConfig(
            total_duration, radius, coords, magnitude_bounds
        )
        source = sources.USGSSource(config)

        poster = sasquatch.BackpackDispatcher(
            source, sasquatch.DispatcherConfig()
        )

        click.echo(poster.post())


if __name__ == "__main__":
    main()
