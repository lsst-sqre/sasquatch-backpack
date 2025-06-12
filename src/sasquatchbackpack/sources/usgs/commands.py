"""USGS CLI."""

import os
from datetime import UTC, datetime, timedelta

import click

from sasquatchbackpack import sasquatch
from sasquatchbackpack.sources.usgs import scripts

DEFAULT_RADIUS = 400

DEFAULT_COORDS = (-30.22573200864174, -70.73932987127506)

DEFAULT_MAGNITUDE_BOUNDS = (2, 10)

# ruff: noqa:TD002
# ruff: noqa:TD003


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
    "--post",
    is_flag=True,
    default=False,
    help=(
        "Allows the user to specify that the API output should be "
        "posted to kafka"
    ),
)
def usgs_earthquake_data(
    duration: tuple[int, int],
    radius: int,
    coords: tuple[float, float],
    magnitude_bounds: tuple[int, int],
    post: bool,  # noqa: FBT001
) -> None:
    """Seaches USGS databases for relevant earthquake data and prints it
    to console. Optionally, also allows the user to post the
    queried data to kafka.
    """
    click.echo(
        f"Querying USGS with post mode {'enabled' if post else 'disabled'}..."
    )

    days, hours = duration
    total_duration = timedelta(days=days, hours=hours)

    config = scripts.USGSConfig(
        total_duration, radius, coords, magnitude_bounds
    )
    source = scripts.USGSSource(config)
    backpack_dispatcher = sasquatch.BackpackDispatcher(source)

    results = scripts.search_api(
        total_duration,
        radius,
        coords,
        magnitude_bounds,
    )

    # TODO: Add CLI feedback on what items are cached to redis
    # and which are new
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

    if not post:
        click.echo("Post mode is disabled: No data will be sent to Kafka.")
        return

    click.echo("Post mode enabled: Sending data...")
    click.echo(f"Querying redis at {backpack_dispatcher.redis.address}")
    click.echo(
        os.getenv(
            "SASQUATCH_REST_PROXY_URL",
            "no env var :(",
        )
    )
    result, records = backpack_dispatcher.post()

    if "Error" in result:
        click.secho(result, fg="red")
    elif "Warning" in result:
        click.secho(result, fg="yellow")
    else:
        click.secho("Data successfully sent!", fg="green")
        click.echo("The following items were added to Kafka:")

        click.echo("------")
        for record in records:
            value = record["value"]
            click.echo(
                f"{value['id']} "
                f"{
                    datetime.fromtimestamp(
                        value['timestamp'], tz=UTC
                    ).strftime('%Y-%m-%d %H:%M:%S')
                } "
                f"({value['latitude']},{value['longitude']}) "
                f"{value['depth']} km "
                f"M{value['magnitude']}"
            )
        click.echo("------")

        click.echo(
            "All entries missing from this list "
            "have been identified as already present in Kafka."
        )
