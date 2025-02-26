"""Backpack CLI."""

import click

from sasquatchbackpack.sources.usgs import commands as usgs


@click.group(context_settings={"help_option_names": ["-h", "--help"]})
@click.version_option(message="%(version)s")
def main() -> None:
    """Command-line interface for sasquatchbackpack."""


main.add_command(usgs.usgs_earthquake_data)
