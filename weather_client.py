import httpx
import asyncio
import statistics
from datetime import datetime, timedelta, date, timezone
from fastapi import HTTPException
from typing import Dict, Any, List, Optional
import schemas  
from weather_cache import get_cached_weather, set_cached_weather, invalidate_trip_cache


GEOCODING_API_URL = "https://geocoding-api.open-meteo.com/v1/search"
WEATHER_API_URL_ARCHIVE = "https://archive-api.open-meteo.com/v1/archive"
WEATHER_API_URL_FORECAST = "https://api.open-meteo.com/v1/forecast"
FORECAST_DETAIL_LIMIT_DAYS = 15


async def get_coordinates(location_name: str) -> List[Dict[str, Any]]:
    async with httpx.AsyncClient() as client:
        try:
            response = await client.get(
                GEOCODING_API_URL, 
                params={"name": location_name, "count": 5, "language": "pl"}
            )
            response.raise_for_status()
            data = response.json()
            
            if not data.get("results"): return []
            
            suggestions = []
            for result in data["results"]:
                name = f"{result['name']}"
                if result.get('admin1'): name += f", {result['admin1']}"
                if result['country'] not in name: name += f", {result['country']}"
                
                suggestions.append({
                    "name": name,
                    "latitude": result["latitude"],
                    "longitude": result["longitude"],
                    "timezone": result["timezone"]
                })
            return suggestions
        except Exception as e:
             raise HTTPException(status_code=500, detail=f"Geocoding error: {e}")


async def _process_weather_response(data: Dict[str, Any], is_forecast: bool) -> List[schemas.DailyWeather]:
    daily = data.get("daily", {})
    
    if is_forecast:
        detailed_data = data.get("minutely_15", {})
        step = 4
    else:
        detailed_data = data.get("hourly", {})
        step = 1

    time_list = daily.get("time", [])
    if not time_list:
        return []
    
    days_count = len(time_list)

    
    temps_max = daily.get("temperature_2m_max") or [0.0] * days_count
    temps_min = daily.get("temperature_2m_min") or [0.0] * days_count
    precips = daily.get("precipitation_sum") or [0.0] * days_count
    
    clouds = daily.get("cloud_cover_mean") or daily.get("cloudcover_mean") or [None] * days_count

    
    d_times = detailed_data.get("time", [])
    d_temps = detailed_data.get("temperature_2m", [])
    d_clouds = detailed_data.get("cloud_cover") or detailed_data.get("cloudcover") or []

    result_list = []
    has_details = len(d_times) > 0

    for i, date_str in enumerate(time_list):
        def safe_get(lst, idx, default):
            if lst and idx < len(lst) and lst[idx] is not None: return lst[idx]
            return default

        current_date = date.fromisoformat(date_str)
        
        day_hourly_chart = []
        manual_cloud_sum = 0
        manual_cloud_count = 0

    
        if has_details:
            samples_per_day = 24 * step
            start_idx = i * samples_per_day
            end_idx = start_idx + samples_per_day
            
            if len(d_times) >= end_idx:
                for h_offset in range(0, samples_per_day, step):
                    chunk_start = start_idx + h_offset
                    chunk_end = chunk_start + step
                    
                    chunk_temps = d_temps[chunk_start:chunk_end]
                    chunk_clouds = d_clouds[chunk_start:chunk_end]
                    
                    valid_temps = [x for x in chunk_temps if x is not None]
                    valid_clouds = [x for x in chunk_clouds if x is not None]
                    
                    avg_h_temp = statistics.mean(valid_temps) if valid_temps else 0.0
                    avg_h_cloud = int(statistics.mean(valid_clouds)) if valid_clouds else 0
                    
                    try:
    
                        time_str = d_times[chunk_start].split("T")[1] 
                    except IndexError:
                        time_str = "00:00"

                    day_hourly_chart.append(schemas.HourlyWeatherPoint(
                        time=time_str,
                        temp=round(avg_h_temp, 1),
                        cloud_cover=avg_h_cloud
                    ))

                    if valid_clouds:
                        manual_cloud_sum += sum(valid_clouds)
                        manual_cloud_count += len(valid_clouds)

    
        daily_cloud_val = safe_get(clouds, i, None)
        if daily_cloud_val is None:
            if manual_cloud_count > 0:
                daily_cloud_val = round(manual_cloud_sum / manual_cloud_count)
            else:
                daily_cloud_val = 0.0

        day_point = schemas.DailyWeather(
            date=current_date,
            temp_max=safe_get(temps_max, i, 0.0),
            temp_min=safe_get(temps_min, i, 0.0),
            precipitation_mm=safe_get(precips, i, 0.0),
            avg_cloud_cover=daily_cloud_val,
            hourly_chart=day_hourly_chart
        )
        result_list.append(day_point)

    return result_list


async def _fetch_chunk(
    client: httpx.AsyncClient, 
    url: str, 
    params: Dict[str, Any], 
    is_forecast: bool
) -> List[schemas.DailyWeather]:
    
    try:
        response = await client.get(url, params=params)
        response.raise_for_status()
        return await _process_weather_response(response.json(), is_forecast)
    except httpx.HTTPStatusError as e:
        if e.response.status_code == 400:
            print(f"Warning: Weather API returned 400 for {params.get('start_date')}. Skipping.")
            return []
        raise e


async def get_average_historical_weather(
    client: httpx.AsyncClient, 
    coords: Dict[str, Any], 
    start_date: datetime,
    end_date: datetime,  
    years_back: int = 5
) -> List[schemas.DailyWeather]:
    tasks = []
    
    for i in range(1, years_back + 1):
        try:
            s_hist = start_date.replace(year=start_date.year - i)
        except ValueError: s_hist = start_date.replace(year=start_date.year - i, day=28)
            
        try:
            e_hist = end_date.replace(year=end_date.year - i)
        except ValueError: e_hist = end_date.replace(year=end_date.year - i, day=28)

        params = {
            "latitude": coords["latitude"],
            "longitude": coords["longitude"],
            "start_date": s_hist.strftime('%Y-%m-%d'),
            "end_date": e_hist.strftime('%Y-%m-%d'),
            "timezone": coords["timezone"],
            "daily": "temperature_2m_max,temperature_2m_min,precipitation_sum", 
            "hourly": "temperature_2m,cloud_cover" 
        }
        tasks.append(_fetch_chunk(client, WEATHER_API_URL_ARCHIVE, params, is_forecast=False))

    results_per_year = await asyncio.gather(*tasks)

    averaged_weather = []
    
    if not results_per_year or not results_per_year[0]:
        return []

    num_days = len(results_per_year[0])

    for day_idx in range(num_days):
        temps_max = []
        temps_min = []
        precips = []
        clouds = []
    
        for year_data in results_per_year:
            if year_data and len(year_data) > day_idx:
                day = year_data[day_idx]
                temps_max.append(day.temp_max)
                temps_min.append(day.temp_min)
                precips.append(day.precipitation_mm)
                clouds.append(day.avg_cloud_cover)

        avg_max = statistics.mean(temps_max) if temps_max else 0.0
        avg_min = statistics.mean(temps_min) if temps_min else 0.0
        avg_precip = statistics.mean(precips) if precips else 0.0
        avg_cloud = statistics.mean(clouds) if clouds else 0.0

        target_future_date = start_date.date() + timedelta(days=day_idx)

        averaged_weather.append(schemas.DailyWeather(
            date=target_future_date, 
            temp_max=round(avg_max, 1),
            temp_min=round(avg_min, 1),
            precipitation_mm=round(avg_precip, 1),
            avg_cloud_cover=int(avg_cloud),
            hourly_chart=[] 
        ))

    return averaged_weather


async def get_weather_data(coords: Dict[str, Any], start_date: datetime, end_date: datetime, is_forecast: bool, trip_id: Optional[int] = None) -> List[schemas.DailyWeather]:
    cached_result = get_cached_weather(
        coords["latitude"],
        coords["longitude"],
        start_date,
        end_date,
        is_forecast,
        schemas.DailyWeather
    )

    if cached_result:
        print("INFO: Zwracam dane z cache (Pydantic objects).")
        return cached_result
    
    async with httpx.AsyncClient() as client:
        
        if not is_forecast:
            result = await get_average_historical_weather(client, coords, start_date, end_date, years_back=5)

            set_cached_weather(
                coords["latitude"],
                coords["longitude"],
                start_date,
                end_date,
                is_forecast,
                result,
                trip_id=trip_id
            )
            return result

        now = datetime.now(timezone.utc).date()
        detail_limit_date = now + timedelta(days=FORECAST_DETAIL_LIMIT_DAYS)
        
        trip_start = start_date.date()
        trip_end = end_date.date()
        
        tasks = []
        
        chunk1_end = min(trip_end, detail_limit_date)
        
        if trip_start <= chunk1_end:
            params_detailed = {
                "latitude": coords["latitude"],
                "longitude": coords["longitude"],
                "start_date": trip_start.strftime('%Y-%m-%d'),
                "end_date": chunk1_end.strftime('%Y-%m-%d'),
                "timezone": coords["timezone"],
                "daily": "temperature_2m_max,temperature_2m_min,precipitation_sum,cloud_cover_mean",
                "minutely_15": "temperature_2m,cloud_cover"
            }
            tasks.append(_fetch_chunk(client, WEATHER_API_URL_FORECAST, params_detailed, is_forecast=True))
        
        chunk2_start_date = chunk1_end + timedelta(days=1)
        chunk2_start_dt = datetime(chunk2_start_date.year, chunk2_start_date.month, chunk2_start_date.day)
        
        if chunk2_start_date <= trip_end:
            tasks.append(
                get_average_historical_weather(
                    client, 
                    coords, 
                    chunk2_start_dt, 
                    end_date, 
                    years_back=5
                )
            )

        try:
            results = await asyncio.gather(*tasks)
            full_weather_list = []
            for res in results:
                full_weather_list.extend(res)
            
            full_weather_list.sort(key=lambda x: x.date)

            final_result: List[schemas.DailyWeather] = full_weather_list

            set_cached_weather(
                coords["latitude"],
                coords["longitude"],
                start_date,
                end_date,
                is_forecast,
                final_result,
                trip_id=trip_id
            )
            return final_result
            
        except Exception as e:
            print(f"Błąd podczas pobierania pogody: {e}")
            raise HTTPException(status_code=500, detail=f"Weather forecast error: {e}")