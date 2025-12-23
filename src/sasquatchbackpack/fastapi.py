"""Backpack FastAPI module."""

from fastapi import FastAPI, Response

from sasquatchbackpack.sources.usgs.commands import usgs_earthquake_data
from sasquatchbackpack.sources.usgs.schemas import EarthquakeRequest

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

    ctx = usgs_earthquake_data.make_context("usgs_earthquake_data", args)
    result = usgs_earthquake_data.invoke(ctx)
    if result.exit_code != 0 or "Error" in result.output:
        response.status_code = 400
    elif "No results found" in result.output:
        response.status_code = 200
