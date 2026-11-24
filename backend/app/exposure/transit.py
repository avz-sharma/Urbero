"""City-level Metro availability, independent of user-entered location labels.

Operational networks: https://sansad.in/getFile/loksabhaquestions/annex/187/AU6274_TyKwGk.pdf?source=pqals
Also: https://www.pib.gov.in/PressReleasePage.aspx?PRID=2240324&lang=1&reg=3
Bounds are approximate service-area screens, not line maps or station catchments.
"""

from typing import Final

METRO_AREAS: Final = (
    (28.35, 28.89, 76.89, 77.56),  # Delhi NCR, including Noida and Gurugram
    (18.89, 19.33, 72.77, 73.13),  # Mumbai and Navi Mumbai
    (22.44, 22.70, 88.25, 88.50),  # Kolkata and Howrah
    (12.80, 13.12, 77.43, 77.79),  # Bengaluru
    (12.96, 13.16, 80.12, 80.31),  # Chennai
    (17.32, 17.52, 78.32, 78.60),  # Hyderabad
    (18.47, 18.67, 73.75, 73.96),  # Pune
    (22.96, 23.27, 72.48, 72.71),  # Ahmedabad and Gandhinagar
    (26.87, 26.96, 75.70, 75.85),  # Jaipur
    (26.74, 26.94, 80.86, 81.01),  # Lucknow
    (26.42, 26.56, 80.22, 80.37),  # Kanpur
    (21.03, 21.20, 78.98, 79.18),  # Nagpur
    (9.92, 10.13, 76.24, 76.37),  # Kochi
    (27.14, 27.22, 77.95, 78.06),  # Agra
    (23.17, 23.27, 77.38, 77.48),  # Bhopal
    (22.72, 22.81, 75.82, 75.95),  # Indore
    (25.56, 25.65, 85.12, 85.29),  # Patna
)


def has_metro(latitude: float, longitude: float) -> bool:
    return any(
        south <= latitude <= north and west <= longitude <= east
        for south, north, west, east in METRO_AREAS
    )
