"""Backpack FastAPI module."""

from fastapi import FastAPI
from pydantic import BaseModel, Field

from sasquatchbackpack.sources.usgs.commands import usgs_earthquake_data

app = FastAPI()


class EarthquakeRequest(BaseModel):
    """Request body for USGS API earthquake query parameters."""

    days: int = Field(
        description="The number of days to look "
        "back from the present when performing the search."
    )
    hours: int = Field(
        description="The number of hours to look "
        "back from the present when performing the search."
    )

    radius: int = Field(
        default=400,
        description="The radius around the provided coordinate to search.",
    )

    latitude: float = Field(
        default=-30.22573200864174,
        description="The latitude of the center coordinate",
    )

    longitude: float = Field(
        default=-70.73932987127506,
        description="The longitude of the center coordinate",
    )

    lower: int = Field(
        default=2,
        description="The lower bound for earthquake magnitude to search",
    )

    upper: int = Field(
        default=10,
        description="The upper bound for earthquake magnitude to search",
    )

    publish: bool = Field(
        default=False,
        description="Whether or not queried data should be published to"
        "sasquatch",
    )

    method: str = Field(
        default="DIRECT_CONNECTION",
        description="The publish method for sending data to sasquatch",
    )


@app.post("/sources/usgs/earthquake/")
async def usgs_earthquake(params: EarthquakeRequest) -> None:
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
    usgs_earthquake_data.invoke(ctx)
