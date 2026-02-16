"""Backpack FastAPI module."""

from contextlib import redirect_stdout
from io import StringIO

import click
from fastapi import FastAPI, Response

from sasquatchbackpack.sources.usgs.commands import usgs_earthquake_data
from sasquatchbackpack.sources.usgs.schemas import EarthquakeRequest

__all__ = ["app"]

app = FastAPI()


@app.post("/sources/usgs/earthquake/", status_code=201)
async def usgs_earthquake(
    params: EarthquakeRequest, response: Response
) -> None:
    """Request to query Earthquake events from the USGS API.

    Parameters
    ----------
    params: EarthquakeRequest
        USGS Query Parameters to POST
    """
    args = [
        "-d",
        f"{params.days}",
        f"{params.hours}",
        "-r",
        f"{params.radius}",
        "-c",
        f"{params.latitude}",
        f"{params.longitude}",
        "-m",
        f"{params.lower}",
        f"{params.upper}",
        "-pm",
        params.method,
    ]

    if params.publish:
        args.append("--publish")

    try:
        ctx = usgs_earthquake_data.make_context("usgs_earthquake_data", args)

        # capture click stdout for error handling
        with redirect_stdout(StringIO()) as out:
            usgs_earthquake_data.invoke(ctx)

    except click.exceptions.BadParameter:
        # improper input
        response.status_code = 400
        return

    if "Error" in out.getvalue():
        # api call/ post failed
        response.status_code = 500

    elif "No results found" in out.getvalue():
        # api returned no results for query
        response.status_code = 204

    elif "publish mode disabled" in out.getvalue():
        # call succeeded, and no data was added to sasquatch
        response.status_code = 200
