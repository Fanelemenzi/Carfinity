"""
Cache utilities for dashboard and notification operations.
Provides Redis caching for expensive operations like vehicle valuation,
inspection results, and health scores.
"""
from django.core.cache import cache
from django.conf import settings
import logging
from typing import Optional, Any, Dict
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)

# Cache TTL settings (in seconds)
VEHICLE_VALUATION_TTL = 24 * 60 * 60  # 24 hours
INSPECTION_RESULTS_TTL = 12 * 60 * 60  # 12 hours
HEALTH_SCORE_TTL = 6 * 60 * 60  # 6 hours
DASHBOARD_DATA_TTL = 30 * 60  # 30 minutes


class CacheManager:
    """Manages caching operations for vehicle dashboard data."""
    
    @staticmethod
    def _get_cache_key(prefix: str, vehicle_id: int, suffix: str = "") -> str:
        """Generate standardized cache key."""
        key = f"vehicle:{vehicle_id}:{prefix}"
        if suffix:
            key += f":{suffix}"
        return key
    
    @staticmethod
    def get_vehicle_valuation(vehicle_id: int) -> Optional[Dict[str, Any]]:
        """Get cached vehicle valuation data."""
        cache_key = CacheManager._get_cache_key("valuation", vehicle_id)
        try:
            return cache.get(cache_key)
        except Exception as e:
            logger.error(f"Error retrieving valuation cache for vehicle {vehicle_id}: {e}")
            return None
    
    @staticmethod
    def set_vehicle_valuation(vehicle_id: int, valuation_data: Dict[str, Any]) -> bool:
        """Cache vehicle valuation data."""
        cache_key = CacheManager._get_cache_key("valuation", vehicle_id)
        try:
            cache.set(cache_key, valuation_data, VEHICLE_VALUATION_TTL)
            logger.info(f"Cached valuation data for vehicle {vehicle_id}")
            return True
        except Exception as e:
            logger.error(f"Error caching valuation for vehicle {vehicle_id}: {e}")
            return False
    
    @staticmethod
    def get_latest_inspection(vehicle_id: int) -> Optional[Dict[str, Any]]:
        """Get cached latest inspection results."""
        cache_key = CacheManager._get_cache_key("inspection", vehicle_id, "latest")
        try:
            return cache.get(cache_key)
        except Exception as e:
            logger.error(f"Error retrieving inspection cache for vehicle {vehicle_id}: {e}")
            return None
    
    @staticmethod
    def set_latest_inspection(vehicle_id: int, inspection_data: Dict[str, Any]) -> bool:
        """Cache latest inspection results."""
        cache_key = CacheManager._get_cache_key("inspection", vehicle_id, "latest")
        try:
            cache.set(cache_key, inspection_data, INSPECTION_RESULTS_TTL)
            logger.info(f"Cached inspection data for vehicle {vehicle_id}")
            return True
        except Exception as e:
            logger.error(f"Error caching inspection for vehicle {vehicle_id}: {e}")
            return False
    
    @staticmethod
    def get_health_score(vehicle_id: int) -> Optional[Dict[str, Any]]:
        """Get cached health score data."""
        cache_key = CacheManager._get_cache_key("health_score", vehicle_id)
        try:
            return cache.get(cache_key)
        except Exception as e:
            logger.error(f"Error retrieving health score cache for vehicle {vehicle_id}: {e}")
            return None
    
    @staticmethod
    def set_health_score(vehicle_id: int, health_data: Dict[str, Any]) -> bool:
        """Cache health score data."""
        cache_key = CacheManager._get_cache_key("health_score", vehicle_id)
        try:
            cache.set(cache_key, health_data, HEALTH_SCORE_TTL)
            logger.info(f"Cached health score for vehicle {vehicle_id}")
            return True
        except Exception as e:
            logger.error(f"Error caching health score for vehicle {vehicle_id}: {e}")
            return False
    
    @staticmethod
    def get_dashboard_data(vehicle_id: int, user_id: int) -> Optional[Dict[str, Any]]:
        """Get cached dashboard data for a specific user and vehicle."""
        cache_key = CacheManager._get_cache_key("dashboard", vehicle_id, f"user:{user_id}")
        try:
            return cache.get(cache_key)
        except Exception as e:
            logger.error(f"Error retrieving dashboard cache for vehicle {vehicle_id}, user {user_id}: {e}")
            return None
    
    @staticmethod
    def set_dashboard_data(vehicle_id: int, user_id: int, dashboard_data: Dict[str, Any]) -> bool:
        """Cache dashboard data for a specific user and vehicle."""
        cache_key = CacheManager._get_cache_key("dashboard", vehicle_id, f"user:{user_id}")
        try:
            cache.set(cache_key, dashboard_data, DASHBOARD_DATA_TTL)
            logger.info(f"Cached dashboard data for vehicle {vehicle_id}, user {user_id}")
            return True
        except Exception as e:
            logger.error(f"Error caching dashboard data for vehicle {vehicle_id}, user {user_id}: {e}")
            return False
    
    @staticmethod
    def invalidate_vehicle_cache(vehicle_id: int) -> bool:
        """Invalidate all cached data for a vehicle."""
        cache_keys = [
            CacheManager._get_cache_key("valuation", vehicle_id),
            CacheManager._get_cache_key("inspection", vehicle_id, "latest"),
            CacheManager._get_cache_key("health_score", vehicle_id),
        ]
        
        try:
            cache.delete_many(cache_keys)
            logger.info(f"Invalidated cache for vehicle {vehicle_id}")
            return True
        except Exception as e:
            logger.error(f"Error invalidating cache for vehicle {vehicle_id}: {e}")
            return False
    
    @staticmethod
    def invalidate_user_dashboard_cache(vehicle_id: int, user_id: int) -> bool:
        """Invalidate dashboard cache for a specific user and vehicle."""
        cache_key = CacheManager._get_cache_key("dashboard", vehicle_id, f"user:{user_id}")
        try:
            cache.delete(cache_key)
            logger.info(f"Invalidated dashboard cache for vehicle {vehicle_id}, user {user_id}")
            return True
        except Exception as e:
            logger.error(f"Error invalidating dashboard cache for vehicle {vehicle_id}, user {user_id}: {e}")
            return False


def cache_vehicle_data(func):
    """
    Decorator to cache expensive vehicle data operations.
    Use this decorator on methods that fetch expensive data like valuations or inspections.
    """
    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except Exception as e:
            logger.error(f"Error in cached function {func.__name__}: {e}")
            raise
    return wrapper


def warm_cache_for_vehicle(vehicle_id: int) -> bool:
    """
    Warm up cache for a vehicle by pre-loading commonly accessed data.
    This can be called after vehicle data updates to ensure fast access.
    """
    try:
        # Import at runtime to avoid circular import issues
        from notifications.services import DashboardService
        
        # Pre-load valuation data
        dashboard_service = DashboardService()
        valuation_data = dashboard_service.get_vehicle_valuation(vehicle_id)
        if valuation_data:
            CacheManager.set_vehicle_valuation(vehicle_id, valuation_data)
        
        logger.info(f"Cache warmed for vehicle {vehicle_id}")
        return True
    except ImportError as e:
        logger.warning(f"Could not import DashboardService for cache warming: {e}")
        return False
    except Exception as e:
        logger.error(f"Error warming cache for vehicle {vehicle_id}: {e}")
        return False