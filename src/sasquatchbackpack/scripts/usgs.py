from datetime import datetime, timedelta

from libcomcat.search import search


def search_api(
    duration: timedelta,
    radius: int = 400,
    coords: tuple[float, float] = (-30.22573200864174, -70.73932987127506),
    min_magnitude: int = 2,
    max_magnitude: int = 10,
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
    current_dt = datetime.now()

    km_radius_events = search(
        starttime=current_dt - duration,
        endtime=current_dt,
        maxradiuskm=radius,
        latitude=coords[0],
        longitude=coords[1],
        minmagnitude=min_magnitude,
        maxmagnitude=max_magnitude,
    )

    return km_radius_events
