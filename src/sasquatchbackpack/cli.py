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
    issues = []

    if radius > 5000:
        issues.append(
            f"Your provided radius ({radius}) is too large. The maximum"
            + " is 5000."
        )
    elif radius <= 0:
        issues.append(
            f"Your provided radius ({radius}) is too small. The minimum"
            + " is 0.1."
        )

    if coords[0] < -90.0:
        issues.append(
            f"Your provided latitude ({coords[0]}) is too low. The"
            + " minimum is -90."
        )
    elif coords[0] > 90.0:
        issues.append(
            f"Your provided latitude ({coords[0]}) is too high. The"
            + " maximum is 90."
        )

    if coords[1] < -180:
        issues.append(
            f"Your provided longitude ({coords[1]}) is too low. The"
            + " minimum is -180."
        )
    elif coords[1] > 180:
        issues.append(
            f"Your provided longitude ({coords[1]}) is too high. The"
            + " maximum is 180."
        )

    if min_magnitude < 0:
        issues.append(
            f"Your provided minimum magnitude ({min_magnitude}) is too"
            + " small. The minimum is 0."
        )
    elif min_magnitude > 10:
        issues.append(
            f"Your provided minimum magnitude ({min_magnitude}) is too"
            + "large. The maximum is 10."
        )

    if max_magnitude > 10:
        issues.append(
            f"Your provided maximum magnitude ({max_magnitude}) is too"
            + " large. The maximum is 10."
        )
    elif max_magnitude < 0:
        issues.append(
            f"Your provided maximum magnitude ({max_magnitude}) is too"
            + " small. The minimum is 0."
        )

    if min_magnitude > max_magnitude:
        issues.append(
            f"Your provided minimum magnitude ({min_magnitude}) cannot"
            + " excede your provided maximum magnitude ({max_magnitude})."
        )

    if len(issues) > 0:
        click.secho(
            "Command Failed! One or more provided parameters is \
            incorrect.\n",
            fg="red",
        )
        if len(issues) == 1:
            click.echo("ISSUE\n------")
            click.echo(issues[0])
            click.echo("------")
        else:
            click.echo("ISSUES\n------")
            for issue in issues:
                click.echo(issue)
            click.echo("------")
        return

    results = usgs.search_api(
        timedelta(duration[0], 0, 0, 0, 0, duration[1], 0),
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
        click.echo("No results found for the provided criteria :(")


if __name__ == "__main__":
    main()
