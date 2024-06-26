"""Accesses the USGSLibcomcat API."""

from datetime import datetime, timedelta

from libcomcat.search import search


def search_api(
    duration: timedelta,
    radius: int = 400,
    coords: tuple[float, float] = (-30.22573200864174, -70.73932987127506),
    magnitude_bounds: tuple[int, int] = (2, 10),
) -> list:
    """Seaches USGS databases for relevant earthquake data.

    Parameters
    ----------
        duration (datetime.timedelta): How far back from the present
            should be searched.
        radius (int, optional): radius of search from central
            coordinates in km. Defaults to 400km.
        coords (tuple(float,float), optional): latitude and longitude of
            the central coordnates. Latitude is first and Longitude is
            second. Defaults to the latitude and longitude of Cerro
            Pachon.
        min_magnitude (int, optional): minimum earthquake magnitude.
            Defaults to 2.
        max_magnitude (int, optional): maximum earthquake magnitude.
            Defaults to 10.
    """
    # Linting bypassed, as at the time of writing Libcomcat breaks if provided
    # with a timezone-aware datetime object
    current_dt = datetime.utcnow()  # noqa: DTZ003

    return search(
        starttime=current_dt - duration,
        endtime=current_dt,
        maxradiuskm=radius,
        latitude=coords[0],
        longitude=coords[1],
        minmagnitude=magnitude_bounds[0],
        maxmagnitude=magnitude_bounds[1],
    )
