from datetime import timedelta

import click

from sasquatchbackpack.scripts import usgs

global radius_default
radius_default = 400

global coords_default
coords_default = (-30.22573200864174, -70.73932987127506)

global magnitude_bounds
magnitude_bounds = (2, 10)


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


def check_min_magnitude(ctx: click.Context, param: dict, value: int) -> int:
    """Validate minimum magnitude"""
    if value < 0:
        raise click.BadParameter(
            f"""Your provided minimum magnitude ({value}) is
 too small. The minimum is 0."""
        )
    elif value > 10:
        raise click.BadParameter(
            f"""Your provided minimum magnitude ({value}) is
 too large. The maximum is 10."""
        )

    return value


def check_max_magnitude(ctx: click.Context, param: dict, value: int) -> int:
    """Validate maximum magnitude"""
    if value > 10:
        raise click.BadParameter(
            f"""Your provided maximum magnitude ({value}) is
 too large. The maximum is 10."""
        )
    elif value < 0:
        raise click.BadParameter(
            f"""Your provided maximum magnitude ({value}) is
 too small. The minimum is 0."""
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
    help="How far back from the present should be searched in days,"
    + " then hours.",
    required=True,
    type=(int, int),
    callback=check_duration,
)
@click.option(
    "-r",
    "--radius",
    help="radius of search from central coordinates in km.",
    default=radius_default,
    type=int,
    show_default=True,
    callback=check_radius,
)
@click.option(
    "-c",
    "--coords",
    help="latitude and longitude of the central coordnates. Latitude"
    + " is first and Longitude is second. Defaults to the"
    + " coordinates of Cerro Pachon.",
    default=coords_default,
    type=(float, float),
    show_default=True,
    callback=check_coords,
)
@click.option(
    "-mm",
    "--min-magnitude",
    help="minimum earthquake magnitude.",
    default=magnitude_bounds[0],
    type=int,
    show_default=True,
    callback=check_min_magnitude,
)
@click.option(
    "-xm",
    "--max-magnitude",
    help="maximum earthquake magnitude.",
    default=magnitude_bounds[1],
    type=int,
    show_default=True,
    callback=check_max_magnitude,
)
def usgs_earthquake_data(
    duration: tuple[int, int],
    radius: int,
    coords: tuple[float, float],
    min_magnitude: int,
    max_magnitude: int,
) -> None:
    """Seaches USGS databases for relevant earthquake data and prints it
    to console
    """
    if min_magnitude > max_magnitude:
        raise click.BadParameter(
            f"""Your provided minimum magnitude ({min_magnitude})
cannot excede your provided maximum magnitude ({max_magnitude})."""
        )

    total_duration = timedelta(duration[0], 0, 0, 0, 0, duration[1], 0)

    results = usgs.search_api(
        total_duration,
        radius,
        coords,
        min_magnitude,
        max_magnitude,
    )

    if len(results) > 0:
        click.secho("SUCCESS!", fg="green")
        click.echo("------")
        for result in results:
            click.echo(result)
        click.echo("------")
    else:
        click.secho("SUCCESS", fg="orange")
        click.echo("------")
        click.echo("No results found for the provided criteria :(")
        click.echo("------")
