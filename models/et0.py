"""FAO-56 Penman-Monteith reference evapotranspiration (ET0) engine.

Implements the standard FAO-56 Penman-Monteith methodology for calculating reference
crop evapotranspiration ET0 across minute, hourly, and daily temporal scales.

Standard FAO-56 Reference Method (Chapter 2 & Chapter 4):
    Daily:
        ET0 = [ 0.408 * Delta * (Rn - G) + gamma * (900 / (T + 273)) * u2 * (es - ea) ] /
              [ Delta + gamma * (1 + 0.34 * u2) ]

    Hourly / Sub-daily:
        ET0_hr = [ 0.408 * Delta * (Rn - G) + gamma * (37 / (T + 273)) * u2 * (es - ea) ] /
                 [ Delta + gamma * (1 + 0.34 * u2) ]

Where:
    ET0: Reference evapotranspiration [mm/day or mm/hour]
    Rn: Net radiation at crop surface [MJ/(m2*day) or MJ/(m2*hour)]
    G: Soil heat flux density [MJ/(m2*day) or MJ/(m2*hour)]
    T: Mean air temperature at 2 m height [°C]
    u2: Wind speed at 2 m height [m/s]
    es: Saturation vapour pressure [kPa]
    ea: Actual vapour pressure [kPa]
    es - ea: Vapour pressure deficit (VPD) [kPa]
    Delta: Slope of saturation vapour pressure curve [kPa/°C]
    gamma: Psychrometric constant [kPa/°C]
"""

from typing import Optional, Union, Tuple
import numpy as np
import pandas as pd


# Physical Constants (FAO-56 Annex 2)
SOLAR_CONSTANT_GSC = 0.0820  # MJ / (m2 * min) extraterrestrial solar constant
STEFAN_BOLTZMANN_DAILY = 4.903e-9   # MJ / (K4 * m2 * day)
STEFAN_BOLTZMANN_HOURLY = 2.043e-10  # MJ / (K4 * m2 * hour)
STANDARD_ALBEDO_GRASS = 0.23        # Dimensionless reflection coefficient
DEFAULT_ELEVATION_M = 53.0          # Ahmedabad baseline elevation (m above sea level)
DEFAULT_LATITUDE_DEG = 23.02        # Ahmedabad baseline latitude (°N)


def calculate_atmospheric_pressure(elevation_m: float = DEFAULT_ELEVATION_M) -> float:
    """Calculate atmospheric pressure as a function of elevation according to FAO-56 Eq. 7.

    P = 101.3 * ((293.0 - 0.0065 * z) / 293.0) ** 5.26

    Args:
        elevation_m: Elevation above sea level in meters (z). Default 53.0 m.

    Returns:
        float: Atmospheric pressure P in kPa.
    """
    z = max(-100.0, float(elevation_m))
    temp_term = (293.0 - 0.0065 * z) / 293.0
    if temp_term <= 0.0:
        return 101.3
    return float(101.3 * (temp_term ** 5.26))


def calculate_psychrometric_constant(
    atmospheric_pressure_kpa: float = 101.3,
) -> float:
    """Calculate the psychrometric constant according to FAO-56 Eq. 8.

    gamma = 0.665e-3 * P

    Args:
        atmospheric_pressure_kpa: Atmospheric pressure in kPa.

    Returns:
        float: Psychrometric constant gamma in kPa/°C.
    """
    return float(0.665e-3 * max(10.0, float(atmospheric_pressure_kpa)))


def calculate_saturation_vapor_pressure(temperature_c: float) -> float:
    """Calculate saturation vapour pressure at air temperature T according to FAO-56 Eq. 11.

    e°(T) = 0.6108 * exp((17.27 * T) / (T + 237.3))

    Args:
        temperature_c: Air temperature in °C.

    Returns:
        float: Saturation vapour pressure in kPa.
    """
    t = float(temperature_c)
    return float(0.6108 * np.exp((17.27 * t) / (t + 237.3)))


def calculate_actual_vapor_pressure(
    temperature_c: float,
    humidity_percent: float,
) -> float:
    """Calculate actual vapour pressure from temperature and relative humidity (FAO-56 Eq. 17).

    ea = e°(T) * (RH / 100)

    Args:
        temperature_c: Air temperature in °C.
        humidity_percent: Relative humidity in percent (0 - 100%).

    Returns:
        float: Actual vapour pressure in kPa.
    """
    es = calculate_saturation_vapor_pressure(temperature_c)
    rh_frac = np.clip(float(humidity_percent) / 100.0, 0.0, 1.0)
    return float(es * rh_frac)


def calculate_vpd(temperature_c: float, humidity_percent: float) -> float:
    """Calculate atmospheric vapour pressure deficit (VPD).

    VPD = max(0.0, es - ea)

    Args:
        temperature_c: Air temperature in °C.
        humidity_percent: Relative humidity in percent (0 - 100%).

    Returns:
        float: Vapour pressure deficit in kPa.
    """
    es = calculate_saturation_vapor_pressure(temperature_c)
    ea = calculate_actual_vapor_pressure(temperature_c, humidity_percent)
    return float(max(0.0, es - ea))


def calculate_slope_vapor_pressure_curve(temperature_c: float) -> float:
    """Calculate the slope of the saturation vapour pressure curve (FAO-56 Eq. 13).

    Delta = (4098.0 * (0.6108 * exp((17.27 * T) / (T + 237.3)))) / ((T + 237.3) ** 2)

    Args:
        temperature_c: Air temperature in °C.

    Returns:
        float: Slope of saturation vapour pressure curve Delta in kPa/°C.
    """
    t = float(temperature_c)
    es = calculate_saturation_vapor_pressure(t)
    return float((4098.0 * es) / ((t + 237.3) ** 2))


def convert_wind_height(
    wind_speed_measured: float,
    measurement_height_m: float = 2.0,
) -> float:
    """Adjust wind speed measured at elevation z to standard 2m height (FAO-56 Eq. 47).

    u2 = uz * (4.87 / ln(67.8 * zw - 5.42))

    When measurement_height_m == 2.0, u2 = uz directly.

    Args:
        wind_speed_measured: Wind speed in m/s.
        measurement_height_m: Measurement sensor height in meters. Default 2.0 m.

    Returns:
        float: Wind speed at 2 m height u2 in m/s.
    """
    uz = max(0.0, float(wind_speed_measured))
    if abs(measurement_height_m - 2.0) < 1e-4:
        return uz
    zw = max(0.5, float(measurement_height_m))
    denom = np.log(67.8 * zw - 5.42)
    return float(max(0.0, uz * (4.87 / denom)))


def calculate_extraterrestrial_radiation_hourly(
    latitude_deg: float = DEFAULT_LATITUDE_DEG,
    day_of_year: int = 152,  # June 1 baseline
    hour_of_day: float = 12.0,
) -> float:
    """Calculate extraterrestrial radiation Ra for an hourly period (FAO-56 Eq. 28, 48).

    Args:
        latitude_deg: Latitude in decimal degrees (positive for North).
        day_of_year: Julian day of year J (1 to 365/366).
        hour_of_day: Decimal hour of the day (0.0 to 24.0).

    Returns:
        float: Extraterrestrial radiation Ra in MJ/(m2 * hour).
    """
    phi = np.radians(latitude_deg)
    # Inverse relative distance Earth-Sun (Eq. 23)
    dr = 1.0 + 0.033 * np.cos(2.0 * np.pi * day_of_year / 365.0)
    # Solar declination (Eq. 24)
    delta = 0.409 * np.sin((2.0 * np.pi * day_of_year / 365.0) - 1.39)
    # Solar time angle at midpoint of hour (Eq. 31)
    # Solar noon assumed at 12:00
    omega = (np.pi / 12.0) * (hour_of_day - 12.0)
    omega1 = omega - (np.pi / 24.0)
    omega2 = omega + (np.pi / 24.0)

    # Sunset hour angle (Eq. 25)
    cos_ws = -np.tan(phi) * np.tan(delta)
    if cos_ws < -1.0:
        ws = np.pi  # Polar day
    elif cos_ws > 1.0:
        ws = 0.0   # Polar night
    else:
        ws = np.arccos(cos_ws)

    # Check daylight limits
    if omega1 < -ws:
        omega1 = -ws
    if omega2 > ws:
        omega2 = ws
    if omega1 >= omega2:
        return 0.0

    # Hourly Ra (Eq. 48) in MJ/(m2*hour)
    # 12 * 60 / pi * Gsc = 720 / pi * 0.0820 = 18.7938
    ra = (
        (12.0 * 60.0 / np.pi)
        * SOLAR_CONSTANT_GSC
        * dr
        * (
            (omega2 - omega1) * np.sin(phi) * np.sin(delta)
            + np.cos(phi) * np.cos(delta) * (np.sin(omega2) - np.sin(omega1))
        )
    )
    return float(max(0.0, ra))


def calculate_clear_sky_radiation(
    ra_mj_m2: float,
    elevation_m: float = DEFAULT_ELEVATION_M,
) -> float:
    """Calculate clear-sky solar radiation Rso from Ra and elevation (FAO-56 Eq. 37).

    Rso = (0.75 + 2e-5 * z) * Ra

    Args:
        ra_mj_m2: Extraterrestrial radiation in MJ/m2 (hourly or daily).
        elevation_m: Station elevation in meters.

    Returns:
        float: Clear-sky solar radiation Rso in MJ/m2.
    """
    z = max(0.0, float(elevation_m))
    coef = 0.75 + (2e-5 * z)
    return float(max(0.0, coef * float(ra_mj_m2)))


def calculate_net_shortwave_radiation(
    solar_radiation_mj_m2: float,
    albedo: float = STANDARD_ALBEDO_GRASS,
) -> float:
    """Calculate net shortwave radiation Rns according to FAO-56 Eq. 38.

    Rns = (1 - albedo) * Rs

    Args:
        solar_radiation_mj_m2: Incoming global solar radiation Rs in MJ/m2.
        albedo: Reflection coefficient (albedo). Default 0.23 for reference grass.

    Returns:
        float: Net shortwave radiation Rns in MJ/m2.
    """
    rs = max(0.0, float(solar_radiation_mj_m2))
    return float((1.0 - float(albedo)) * rs)


def calculate_net_longwave_radiation(
    temperature_c: float,
    actual_vapor_pressure_kpa: float,
    solar_radiation_mj_m2: float,
    clear_sky_radiation_mj_m2: float,
    timestep_hours: float = 1.0,
) -> float:
    """Calculate net longwave radiation Rnl according to FAO-56 Eq. 39 & Eq. 55.

    Rnl = sigma * (T_kelvin ** 4) * (0.34 - 0.14 * sqrt(ea)) * (1.35 * (Rs / Rso) - 0.35)

    Args:
        temperature_c: Mean air temperature in °C.
        actual_vapor_pressure_kpa: Actual vapour pressure ea in kPa.
        solar_radiation_mj_m2: Observed global solar radiation Rs in MJ/m2 over timestep.
        clear_sky_radiation_mj_m2: Clear-sky radiation Rso in MJ/m2 over timestep.
        timestep_hours: Timestep duration in hours (1.0 for hourly, 24.0 for daily, 1/60 for min).

    Returns:
        float: Net longwave radiation Rnl in MJ/m2 over the timestep.
    """
    t_k = float(temperature_c) + 273.16
    ea = max(0.0, float(actual_vapor_pressure_kpa))
    rs = max(0.0, float(solar_radiation_mj_m2))
    rso = max(1e-4, float(clear_sky_radiation_mj_m2))

    # Determine Stefan-Boltzmann constant scaled to duration
    # Hourly constant is 2.043e-10 MJ/(m2*K4*h)
    sigma = STEFAN_BOLTZMANN_HOURLY * float(timestep_hours)

    # Cloudiness / relative radiation fraction
    if clear_sky_radiation_mj_m2 > 0.05 and rs > 0.0:
        rs_rso = np.clip(rs / rso, 0.30, 1.0)
    else:
        # Nighttime or very low sun: assume standard clear/partly-cloudy night ratio ~0.75
        rs_rso = 0.75

    cloudiness_factor = np.clip(1.35 * rs_rso - 0.35, 0.05, 1.0)
    humidity_factor = max(0.01, 0.34 - 0.14 * np.sqrt(ea))

    rnl = sigma * (t_k ** 4) * humidity_factor * cloudiness_factor
    return float(max(0.0, rnl))


def calculate_net_radiation(
    solar_radiation_wm2: float,
    temperature_c: float,
    humidity_percent: float,
    timestep_minutes: int = 1,
    elevation_m: float = DEFAULT_ELEVATION_M,
    latitude_deg: float = DEFAULT_LATITUDE_DEG,
    day_of_year: int = 152,
    hour_of_day: float = 12.0,
) -> Tuple[float, float, float]:
    """Compute complete net radiation Rn, net shortwave Rns, and net longwave Rnl.

    Converts W/m2 to MJ/m2 over the timestep duration:
        Energy [MJ/m2] = Radiation [W/m2] * (timestep_minutes * 60) * 1e-6

    Returns:
        Tuple[float, float, float]: (Rn, Rns, Rnl) in MJ/m2 for the timestep.
    """
    timestep_seconds = float(timestep_minutes) * 60.0
    timestep_hours = float(timestep_minutes) / 60.0

    # Solar energy over timestep
    rs_mj = max(0.0, float(solar_radiation_wm2)) * timestep_seconds * 1e-6
    rns_mj = calculate_net_shortwave_radiation(rs_mj)

    # Theoretical clear sky radiation
    ra_hr = calculate_extraterrestrial_radiation_hourly(latitude_deg, day_of_year, hour_of_day)
    ra_step = ra_hr * timestep_hours
    rso_step = calculate_clear_sky_radiation(ra_step, elevation_m)

    ea = calculate_actual_vapor_pressure(temperature_c, humidity_percent)
    rnl_mj = calculate_net_longwave_radiation(
        temperature_c=temperature_c,
        actual_vapor_pressure_kpa=ea,
        solar_radiation_mj_m2=rs_mj,
        clear_sky_radiation_mj_m2=rso_step,
        timestep_hours=timestep_hours,
    )

    rn_mj = rns_mj - rnl_mj
    return float(rn_mj), float(rns_mj), float(rnl_mj)


def calculate_soil_heat_flux(
    net_radiation_mj_m2: float,
    is_daylight: bool = True,
    daily: bool = False,
) -> float:
    """Calculate soil heat flux density G according to FAO-56 Chapter 3 & 4.

    Daily (FAO-56 Eq. 42):
        G ≈ 0.0 MJ/(m2 * day)

    Sub-daily / Hourly (FAO-56 Eq. 45 & 46):
        Daylight (Rn > 0): G = 0.10 * Rn
        Nighttime (Rn <= 0): G = 0.50 * Rn

    Args:
        net_radiation_mj_m2: Net radiation Rn in MJ/m2 over the period.
        is_daylight: True during daytime periods, False during nighttime.
        daily: Set True for daily aggregation where G ≈ 0.

    Returns:
        float: Soil heat flux density G in MJ/m2.
    """
    if daily:
        return 0.0

    rn = float(net_radiation_mj_m2)
    if is_daylight and rn > 0.0:
        return float(0.10 * rn)
    else:
        return float(0.50 * rn)


def calculate_et0_fao56(
    temperature_c: float,
    humidity_percent: float,
    solar_radiation_wm2: float = 0.0,
    wind_speed_ms: float = 2.0,
    atmospheric_pressure_kpa: Optional[float] = None,
    soil_heat_flux_g: Optional[float] = None,
    timestep_minutes: int = 1440,
    elevation_m: float = DEFAULT_ELEVATION_M,
    as_step_depth: bool = False,
    latitude_deg: float = DEFAULT_LATITUDE_DEG,
    day_of_year: int = 152,
    hour_of_day: float = 12.0,
    solar_radiation_mj_m2: Optional[float] = None,
    net_radiation_mj_m2: Optional[float] = None,
) -> float:
    """Calculate reference crop evapotranspiration (ET0) using FAO-56 Penman-Monteith.

    Handles both daily standard evaluations and sub-daily (1-min, hourly) timesteps.

    Formulation:
        For daily timestep (1440 min):
            ET0 = [ 0.408 * Delta * (Rn - G) + gamma * (900 / (T + 273)) * u2 * (es - ea) ] /
                  [ Delta + gamma * (1 + 0.34 * u2) ]

        For sub-daily timestep (1 to 60 min):
            ET0_hr = [ 0.408 * Delta * (Rn_hr - G_hr) + gamma * (37 / (T + 273)) * u2 * (es - ea) ] /
                     [ Delta + gamma * (1 + 0.34 * u2) ]
            where Rn_hr and G_hr are scaled to MJ/(m2 * hour).

    Args:
        temperature_c: Mean air temperature (°C).
        humidity_percent: Relative humidity (%).
        solar_radiation_wm2: Downward global solar radiation (W/m2).
        wind_speed_ms: Wind speed at 2 m height (m/s).
        atmospheric_pressure_kpa: Site pressure in kPa (calculated from elevation if None).
        soil_heat_flux_g: Optional user-specified G in MJ/m2. If None, derived by FAO-56.
        timestep_minutes: Time-step duration (1440 = daily, 60 = hourly, 1 = simulation step).
        elevation_m: Site elevation in meters.
        as_step_depth: If True, returns accumulated mm for the specific timestep.
                       If False, returns equivalent rate in mm/day.
        latitude_deg: Geographic latitude in degrees.
        day_of_year: Julian day of year.
        hour_of_day: Decimal hour of the day (0 - 24).
        solar_radiation_mj_m2: Optional direct solar radiation energy in MJ/m2.
        net_radiation_mj_m2: Optional direct net radiation in MJ/m2.

    Returns:
        float: Reference evapotranspiration ET0 in mm/day (or mm/step if as_step_depth=True).
    """
    # 1. Atmospheric pressure & Psychrometric constant
    if atmospheric_pressure_kpa is None:
        p_kpa = calculate_atmospheric_pressure(elevation_m)
    else:
        p_kpa = float(atmospheric_pressure_kpa)
    gamma = calculate_psychrometric_constant(p_kpa)

    # 2. Vapour pressures and slope Delta
    t = float(temperature_c)
    es = calculate_saturation_vapor_pressure(t)
    ea = calculate_actual_vapor_pressure(t, humidity_percent)
    delta = calculate_slope_vapor_pressure_curve(t)
    vpd = max(0.0, es - ea)

    # 3. Wind speed
    u2 = convert_wind_height(wind_speed_ms, measurement_height_m=2.0)

    # 4. Net radiation and soil heat flux
    if net_radiation_mj_m2 is not None:
        rn_step = float(net_radiation_mj_m2)
    elif solar_radiation_mj_m2 is not None:
        rs_mj = float(solar_radiation_mj_m2)
        rns_mj = calculate_net_shortwave_radiation(rs_mj)
        timestep_hours = float(timestep_minutes) / 60.0
        ra_hr = calculate_extraterrestrial_radiation_hourly(latitude_deg, day_of_year, hour_of_day)
        ra_step = ra_hr * timestep_hours
        rso_step = calculate_clear_sky_radiation(ra_step, elevation_m)
        rnl_mj = calculate_net_longwave_radiation(
            temperature_c=t,
            actual_vapor_pressure_kpa=ea,
            solar_radiation_mj_m2=rs_mj,
            clear_sky_radiation_mj_m2=rso_step,
            timestep_hours=timestep_hours,
        )
        rn_step = rns_mj - rnl_mj
    else:
        rn_step, _, _ = calculate_net_radiation(
            solar_radiation_wm2=solar_radiation_wm2,
            temperature_c=t,
            humidity_percent=humidity_percent,
            timestep_minutes=timestep_minutes,
            elevation_m=elevation_m,
            latitude_deg=latitude_deg,
            day_of_year=day_of_year,
            hour_of_day=hour_of_day,
        )

    is_daylight = solar_radiation_wm2 > 1.0 or (solar_radiation_mj_m2 is not None and solar_radiation_mj_m2 > 0.1) or (6.0 <= hour_of_day <= 19.0)

    if soil_heat_flux_g is not None:
        g_step = float(soil_heat_flux_g)
    else:
        g_step = calculate_soil_heat_flux(
            net_radiation_mj_m2=rn_step,
            is_daylight=is_daylight,
            daily=(timestep_minutes >= 1440),
        )

    # 5. Temporal conversion & Penman-Monteith evaluation
    if timestep_minutes >= 1440:
        # Standard daily equation
        # If input solar radiation was in W/m2, scaled to daily MJ/m2
        rn_daily = rn_step
        g_daily = g_step
        num = (0.408 * delta * (rn_daily - g_daily)) + (gamma * (900.0 / (t + 273.0)) * u2 * vpd)
        denom = delta + (gamma * (1.0 + 0.34 * u2))
        et0_daily = max(0.0, float(num / denom))

        if as_step_depth:
            return float(et0_daily * (timestep_minutes / 1440.0))
        return float(et0_daily)
    else:
        # Sub-daily (minute / hourly) equation (FAO-56 Eq. 53)
        # Convert step Rn and G (MJ/m2/step) to hourly equivalent rate (MJ/m2/hour)
        timestep_hours = float(timestep_minutes) / 60.0
        rn_hr = rn_step / timestep_hours
        g_hr = g_step / timestep_hours

        num_hr = (0.408 * delta * (rn_hr - g_hr)) + (gamma * (37.0 / (t + 273.0)) * u2 * vpd)
        denom = delta + (gamma * (1.0 + 0.34 * u2))
        et0_hourly_rate = max(0.0, float(num_hr / denom))  # mm / hour

        # Step depth in mm
        et0_step_depth = et0_hourly_rate * timestep_hours  # mm / step
        et0_daily_equivalent = et0_hourly_rate * 24.0      # mm / day rate

        if as_step_depth:
            return float(et0_step_depth)
        return float(et0_daily_equivalent)


def compute_et0_timeseries(
    df: pd.DataFrame,
    timestep_minutes: int = 1,
    elevation_m: float = DEFAULT_ELEVATION_M,
    latitude_deg: float = DEFAULT_LATITUDE_DEG,
    start_day_of_year: int = 152,
) -> pd.DataFrame:
    """Compute complete FAO-56 meteorological and energy variables for a weather DataFrame.

    Processes timeseries sequentially, populating all intermediate thermodynamic terms:
    - atmospheric_pressure
    - saturation_vapor_pressure
    - actual_vapor_pressure
    - vpd
    - delta
    - gamma
    - net_shortwave_radiation
    - net_longwave_radiation
    - net_radiation
    - soil_heat_flux
    - et0 (mm/step)
    - et0_rate_mm_day (equivalent daily rate)

    Args:
        df: Input DataFrame containing columns ['timestamp', 'temperature', 'humidity',
            'solar_radiation', 'wind_speed', 'rainfall'].
        timestep_minutes: Discretization step in minutes (default 1).
        elevation_m: Station elevation in meters.
        latitude_deg: Geographic latitude in degrees.
        start_day_of_year: Julian day corresponding to row 0.

    Returns:
        pd.DataFrame: Augmented DataFrame with complete ET0 and thermodynamic fields.
    """
    out = df.copy()
    n = len(out)

    # Convert timestamps if available to determine hour of day
    if "timestamp" in out.columns:
        ts = pd.to_datetime(out["timestamp"])
        hour_of_day = ts.dt.hour + (ts.dt.minute / 60.0) + (ts.dt.second / 3600.0)
        day_offset = (ts - ts.iloc[0]).dt.total_seconds() / 86400.0
        day_of_year = start_day_of_year + day_offset.astype(int)
    else:
        # Default step calculation from row index
        step_hours = (np.arange(n) * timestep_minutes) / 60.0
        hour_of_day = step_hours % 24.0
        day_of_year = start_day_of_year + (step_hours // 24).astype(int)

    # Thermodynamic atmospheric parameters
    p_kpa = calculate_atmospheric_pressure(elevation_m)
    gamma = calculate_psychrometric_constant(p_kpa)

    # Vectorized thermodynamic calculations
    temps = out["temperature"].to_numpy(dtype=np.float64)
    rhs = np.clip(out["humidity"].to_numpy(dtype=np.float64), 0.0, 100.0)
    solars = np.maximum(0.0, out["solar_radiation"].to_numpy(dtype=np.float64))
    winds = np.maximum(0.0, out["wind_speed"].to_numpy(dtype=np.float64))

    # Saturation vapour pressure (FAO-56 Eq. 11)
    es = 0.6108 * np.exp((17.27 * temps) / (temps + 237.3))
    # Actual vapour pressure (FAO-56 Eq. 17)
    ea = es * (rhs / 100.0)
    # VPD
    vpd = np.maximum(0.0, es - ea)
    # Slope Delta (FAO-56 Eq. 13)
    delta = (4098.0 * es) / ((temps + 237.3) ** 2)

    # Radiation calculations
    timestep_sec = timestep_minutes * 60.0
    timestep_hr = timestep_minutes / 60.0
    # Solar energy in MJ/m2 per timestep
    rs_mj = solars * timestep_sec * 1e-6
    rns_mj = (1.0 - STANDARD_ALBEDO_GRASS) * rs_mj

    # Extraterrestrial and clear sky radiation array
    rnl_mj = np.zeros(n, dtype=np.float64)
    rn_mj = np.zeros(n, dtype=np.float64)
    g_mj = np.zeros(n, dtype=np.float64)
    et0_step = np.zeros(n, dtype=np.float64)
    et0_rate = np.zeros(n, dtype=np.float64)

    sigma_step = STEFAN_BOLTZMANN_HOURLY * timestep_hr

    for i in range(n):
        h = float(hour_of_day.iloc[i] if hasattr(hour_of_day, "iloc") else hour_of_day[i])
        doy = int(day_of_year.iloc[i] if hasattr(day_of_year, "iloc") else day_of_year[i])

        ra_hr = calculate_extraterrestrial_radiation_hourly(latitude_deg, doy, h)
        rso_step = calculate_clear_sky_radiation(ra_hr * timestep_hr, elevation_m)

        rs_i = rs_mj[i]
        if rso_step > 0.05 and rs_i > 0.0:
            rs_rso = np.clip(rs_i / rso_step, 0.30, 1.0)
        else:
            rs_rso = 0.75

        cloudiness = np.clip(1.35 * rs_rso - 0.35, 0.05, 1.0)
        humidity_term = max(0.01, 0.34 - 0.14 * np.sqrt(ea[i]))
        t_k = temps[i] + 273.16

        rnl_i = sigma_step * (t_k ** 4) * humidity_term * cloudiness
        rn_i = rns_mj[i] - rnl_i

        is_day = solars[i] > 1.0 or (6.0 <= h <= 19.0)
        g_i = 0.10 * rn_i if (is_day and rn_i > 0.0) else 0.50 * rn_i

        # Hourly rate equivalents (MJ/m2/hour)
        rn_hr = rn_i / timestep_hr
        g_hr = g_i / timestep_hr

        # Sub-daily FAO-56 Penman-Monteith (Eq. 53)
        num_hr = (0.408 * delta[i] * (rn_hr - g_hr)) + (
            gamma * (37.0 / (temps[i] + 273.0)) * winds[i] * vpd[i]
        )
        denom = delta[i] + (gamma * (1.0 + 0.34 * winds[i]))
        et0_hr_val = max(0.0, num_hr / denom)

        rnl_mj[i] = rnl_i
        rn_mj[i] = rn_i
        g_mj[i] = g_i
        et0_step[i] = et0_hr_val * timestep_hr
        et0_rate[i] = et0_hr_val * 24.0

    out["atmospheric_pressure"] = np.round(p_kpa, 3)
    out["saturation_vapor_pressure"] = np.round(es, 4)
    out["actual_vapor_pressure"] = np.round(ea, 4)
    out["vpd"] = np.round(vpd, 4)
    out["delta"] = np.round(delta, 5)
    out["gamma"] = np.round(gamma, 5)
    out["net_shortwave_radiation"] = np.round(rns_mj, 6)
    out["net_longwave_radiation"] = np.round(rnl_mj, 6)
    out["net_radiation"] = np.round(rn_mj, 6)
    out["soil_heat_flux"] = np.round(g_mj, 6)
    out["et0"] = np.round(et0_step, 6)  # mm per timestep
    out["et0_rate_mm_day"] = np.round(et0_rate, 4)  # equivalent daily rate (mm/day)

    return out
