"""Backpack FastAPI module."""

from fastapi import FastAPI

from sasquatchbackpack.sources.usgs.commands import usgs_earthquake_data

app = FastAPI()


@app.get(
    "/sources/usgs/earthquake_data/{days}/{hours}/{radius}/{latitude}/{longitude}/{lower}/{upper}/{publish}/{method}"
)
async def read_item(
    days: int,
    hours: int,
    radius: int,
    latitude: int,
    longitude: int,
    lower: int,
    upper: int,
    publish: bool,  # noqa: FBT001
    method: str,
) -> None:
    """Set earthquake_data command."""
    args = [
        "-d",
        f"{days}",
        f"{hours}",
        "-r",
        f"{radius}",
        "-c",
        f"{latitude}",
        f"{longitude}",
        "-m",
        f"{lower}",
        f"{upper}",
        "-pm",
        method,
    ]

    if publish:
        args.append("--publish")

    ctx = usgs_earthquake_data.make_context("usgs_earthquake_data", args)
    usgs_earthquake_data.invoke(ctx)
