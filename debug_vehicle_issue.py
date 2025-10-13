#!/usr/bin/env python
"""
Debug script to identify why users with vehicles are seeing no vehicles message
"""

import os
import sys
import django

# Setup Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'carfinity.settings')
django.setup()

from django.contrib.auth.models import User
from vehicles.models import Vehicle, VehicleOwnership

def debug_vehicle_issue():
    """Debug the vehicle selector issue"""
    
    print("🔍 DEBUGGING VEHICLE SELECTOR ISSUE")
    print("=" * 50)
    
    # Check all users and their vehicles
    print("1. Checking all users and their vehicle ownerships...")
    
    users = User.objects.all()
    print(f"Total users: {users.count()}")
    
    for user in users:
        print(f"\n👤 User: {user.username} (ID: {user.id})")
        
        # Check vehicle ownerships
        ownerships = VehicleOwnership.objects.filter(user=user)
        print(f"   Total ownerships: {ownerships.count()}")
        
        current_ownerships = ownerships.filter(is_current_owner=True)
        print(f"   Current ownerships: {current_ownerships.count()}")
        
        if current_ownerships.exists():
            print("   Current vehicles:")
            for ownership in current_ownerships:
                vehicle = ownership.vehicle
                print(f"     - {vehicle.manufacture_year} {vehicle.make} {vehicle.model} (ID: {vehicle.id})")
        else:
            print("   ❌ No current vehicle ownerships found!")
            
        # Check what get_user_vehicles would return
        user_vehicles = Vehicle.objects.filter(
            ownerships__user=user,
            ownerships__is_current_owner=True
        ).order_by('make', 'model', 'manufacture_year')
        
        print(f"   get_user_vehicles() would return: {user_vehicles.count()} vehicles")
        
        if user_vehicles.exists():
            for vehicle in user_vehicles:
                print(f"     - {vehicle.manufacture_year} {vehicle.make} {vehicle.model}")
    
    # Check template logic conditions
    print("\n2. Checking template logic conditions...")
    
    # Find users with multiple vehicles
    users_with_multiple = []
    users_with_single = []
    users_with_none = []
    
    for user in users:
        user_vehicles = Vehicle.objects.filter(
            ownerships__user=user,
            ownerships__is_current_owner=True
        )
        
        count = user_vehicles.count()
        if count > 1:
            users_with_multiple.append((user, count))
        elif count == 1:
            users_with_single.append((user, count))
        else:
            users_with_none.append((user, count))
    
    print(f"Users with multiple vehicles: {len(users_with_multiple)}")
    for user, count in users_with_multiple:
        print(f"  - {user.username}: {count} vehicles")
    
    print(f"Users with single vehicle: {len(users_with_single)}")
    for user, count in users_with_single:
        print(f"  - {user.username}: {count} vehicle")
    
    print(f"Users with no vehicles: {len(users_with_none)}")
    for user, count in users_with_none:
        print(f"  - {user.username}: {count} vehicles")
    
    # Check specific template conditions
    print("\n3. Template condition analysis...")
    
    for user in users:
        user_vehicles = Vehicle.objects.filter(
            ownerships__user=user,
            ownerships__is_current_owner=True
        ).order_by('make', 'model', 'manufacture_year')
        
        # Template conditions
        has_vehicles = user_vehicles.exists()
        has_multiple = user_vehicles.count() > 1
        
        print(f"\n👤 {user.username}:")
        print(f"   user_vehicles exists: {has_vehicles}")
        print(f"   user_vehicles.count() > 1: {has_multiple}")
        print(f"   Template dropdown condition: {has_vehicles and has_multiple}")
        
        if has_vehicles and not has_multiple:
            print("   ⚠️  Single vehicle user - dropdown won't show (expected)")
        elif has_vehicles and has_multiple:
            print("   ✅ Multiple vehicle user - dropdown should show")
        else:
            print("   ❌ No vehicles - will show no vehicles message")
    
    # Check for data integrity issues
    print("\n4. Data integrity checks...")
    
    # Check for vehicles without current owners
    vehicles_without_owners = Vehicle.objects.exclude(
        ownerships__is_current_owner=True
    )
    print(f"Vehicles without current owners: {vehicles_without_owners.count()}")
    
    # Check for duplicate current ownerships
    from django.db.models import Count
    duplicate_ownerships = VehicleOwnership.objects.filter(
        is_current_owner=True
    ).values('vehicle').annotate(
        count=Count('id')
    ).filter(count__gt=1)
    
    print(f"Vehicles with multiple current owners: {duplicate_ownerships.count()}")
    
    if duplicate_ownerships.exists():
        print("   Vehicles with duplicate ownerships:")
        for dup in duplicate_ownerships:
            vehicle = Vehicle.objects.get(id=dup['vehicle'])
            print(f"     - {vehicle.make} {vehicle.model} (ID: {vehicle.id}) - {dup['count']} owners")
    
    print("\n" + "=" * 50)
    print("🎯 SUMMARY")
    print("=" * 50)
    
    if users_with_multiple:
        print("✅ Users with multiple vehicles exist - dropdown should work for them")
    else:
        print("⚠️  No users with multiple vehicles found - dropdown won't appear")
    
    if users_with_single:
        print("✅ Users with single vehicles exist - they should see vehicle data (no dropdown)")
    
    if users_with_none:
        print("❌ Users with no vehicles will see 'no vehicles' message")
    
    return {
        'users_with_multiple': len(users_with_multiple),
        'users_with_single': len(users_with_single),
        'users_with_none': len(users_with_none),
        'total_users': users.count()
    }

if __name__ == "__main__":
    debug_vehicle_issue()