"""USGS CLI."""

from datetime import timedelta

import click

from sasquatchbackpack import sasquatch
from sasquatchbackpack.scripts import usgs

DEFAULT_RADIUS = 400

DEFAULT_COORDS = (-30.22573200864174, -70.73932987127506)

DEFAULT_MAGNITUDE_BOUNDS = (2, 10)


def check_duration(
    ctx: click.Context, param: dict, value: tuple[int, int]
) -> tuple[int, int]:
    """Validate duration inputs."""
    days, hours = value
    total_duration = timedelta(days=days, hours=hours)

    if total_duration > timedelta(days=10000):
        raise click.BadParameter(
            f"""Your provided duration ({total_duration!s}) is
    too large. The maximum is 10000 days."""
        )
    if total_duration < timedelta(hours=1):
        raise click.BadParameter(
            f"""Your provided duration ({total_duration!s}) is
    too small. The minimum is 1 hour."""
        )

    return value


def check_radius(ctx: click.Context, param: dict, value: int) -> int:
    """Validate radius inputs."""
    if value > 5000:
        raise click.BadParameter(
            f"""Your provided radius ({value}) is too large.
 The maximum is 5000."""
        )
    if value <= 0:
        raise click.BadParameter(
            f"""Your provided radius ({value}) is too small.
 The minimum is 0.1."""
        )

    return value


def check_coords(
    ctx: click.Context, param: dict, value: tuple[float, float]
) -> tuple[float, float]:
    """Validate coords inputs."""
    latitude, longitude = value
    if latitude < -90.0 or latitude > 90.0:
        raise click.BadParameter(
            f"Your provided latitude ({latitude}) is out of bounds."
            "The range is -90 to 90."
        )

    if longitude < -180.0 or longitude > 180.0:
        raise click.BadParameter(
            f"Your provided longitude ({longitude}) is out of bounds."
            "The range is -180 to 180."
        )

    return value


def check_magnitude_bounds(
    ctx: click.Context, param: dict, value: tuple[int, int]
) -> tuple[int, int]:
    """Validate magnitude bounds."""
    lower, upper = value
    if lower < 0 or lower > 10:
        raise click.BadParameter(
            f"Your provided minimum magnitude ({lower}) is "
            "out of bounds. The range is 0 to 10."
        )

    if upper > 10 or upper < 0:
        raise click.BadParameter(
            f"Your provided maximum magnitude ({upper}) is "
            "out of bounds. The range is 0 to 10."
        )

    if lower > upper:
        raise click.BadParameter(
            f"""Your provided minimum magnitude ({lower})
cannot excede your provided maximum magnitude ({upper})."""
        )

    return value


@click.command()
@click.option(
    "-d",
    "--duration",
    help="How far back from the present should be searched (days, hours)",
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
    help="latitude and longitude of the central coordinates "
    "(latitude, longitude). Defaults to the coordinates of Cerro Pachon.",
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
    "--dry-run",
    is_flag=True,
    default=False,
    help="Perform a trial run with no data being sent to Kafka.",
)
def usgs_earthquake_data(
    duration: tuple[int, int],
    radius: int,
    coords: tuple[float, float],
    magnitude_bounds: tuple[int, int],
    dry_run: bool,  # noqa: FBT001
) -> None:
    """Seaches USGS databases for relevant earthquake data and prints it
    to console. Optionally, also allows the user to post the
    queried data to kafka.
    """
    days, hours = duration
    total_duration = timedelta(days=days, hours=hours)

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

    if dry_run:
        click.echo("Dry run mode: No data will be sent to Kafka.")
        return

    click.echo("Sending data...")

    config = usgs.USGSConfig(total_duration, radius, coords, magnitude_bounds)
    source = usgs.USGSSource(config)

    backpack_dispatcher = sasquatch.BackpackDispatcher(
        source, sasquatch.DispatcherConfig()
    )
    result = backpack_dispatcher.post()

    if "Error" in result:
        click.secho(result, fg="red")
    else:
        click.secho("Data successfully sent!", fg="green")
