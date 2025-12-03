"""Backpack FastAPI module."""

from fastapi import FastAPI
from pydantic import BaseModel

from sasquatchbackpack.sources.usgs.commands import usgs_earthquake_data

app = FastAPI()


class EarthquakeParams(BaseModel):
    """{days}/{hours}/{radius}/{latitude}/{longitude}/{lower}/{upper}/{publish}/{method}."""

    days: int
    hours: int
    radius: int
    latitude: int
    longitude: int
    lower: int
    upper: int
    publish: bool
    method: str


@app.post("/sources/usgs/earthquake_data/")
async def read_item(params: EarthquakeParams) -> None:
    """Set earthquake_data command."""
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
