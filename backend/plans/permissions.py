# from rest_framework import permissions
# from .models import ShareLink, Trip

# class CanAccessTrip(permissions.BasePermission):
#     def has_object_permission(self, request, view, obj):
        
#         # find the related Trip object
#         trip = None
#         if isinstance(obj, Trip):
#             trip = obj
#         elif hasattr(obj, 'trip'):
#             trip = obj.trip
#         elif hasattr(obj, 'day'):
#             trip = obj.day.trip
#         if not trip:
#             return False

#         # Check 1: Authenticated user who owns the trip
#         if request.user and request.user.is_authenticated:
#             if trip.user == request.user:
#                 return True

#         # Check 2: ShareLink authentication
#         if request.auth and isinstance(request.auth, ShareLink):
#             share_link = request.auth
            
#             if share_link.trip == trip:
#                 if share_link.permission_level == 'edit':
#                     return True 
#                 if share_link.permission_level == 'read':
#                     return request.method in permissions.SAFE_METHODS 
        
#         return False
# plans/permissions.py

# plans/permissions.py
from rest_framework import permissions
from .models import ShareLink, Trip

class CanAccessTrip(permissions.BasePermission):
    
    def has_permission(self, request, view):
        print("--- [AUTH DEBUG] 运行 has_permission ---")
        
        # --- 检查 1: 已登录用户 (所有者检查) ---
        if request.user and request.user.is_authenticated:
            if 'trip_id' not in view.kwargs:
                # 这是 /api/plans/trips/ (列表视图)，已登录就足够了
                return True
            try:
                trip = Trip.objects.get(pk=view.kwargs['trip_id'])
                if trip.user == request.user:
                    print(f"[AUTH DEBUG] has_permission 成功: 检查所有者: True")
                    return True # 用户是所有者，允许
            except Trip.DoesNotExist:
                print(f"[AUTH DEBUG] has_permission 失败: Trip {view.kwargs['trip_id']} 不存在")
                return False # Trip 不存在
            
            # 如果执行到这里，说明用户已登录但*不是*所有者。
            # 不要立刻返回 False，我们继续检查 ShareLink。
            print(f"[AUTH DEBUG] has_permission 检查所有者: False. 继续检查 ShareLink...")

        # --- 检查 2: 分享链接用户 ---
        if request.auth and isinstance(request.auth, ShareLink):
            share_link = request.auth
            
            if 'trip_id' in view.kwargs:
                try:
                    url_trip_id = int(view.kwargs['trip_id'])
                except ValueError:
                    print(f"[AUTH DEBUG] has_permission 失败: URL trip_id 无效")
                    return False 
                
                if share_link.trip.pk != url_trip_id:
                    print(f"[AUTH DEBUG] has_permission 失败: Token (Trip {share_link.trip.pk}) 与 URL (Trip {url_trip_id}) 不匹配")
                    return False
            
            # 此时, Token 匹配 URL 的 Trip ID。检查权限级别。
            if share_link.permission_level == 'edit':
                print(f"[AUTH DEBUG] has_permission 成功: 'edit' 权限")
                return True # 'edit' 权限允许所有操作
            
            if share_link.permission_level == 'read':
                is_safe = request.method in permissions.SAFE_METHODS
                if not is_safe:
                    print(f"[AUTH DEBUG] has_permission 失败: 'read' Token 试图执行不安全操作 ({request.method})")
                else:
                    print(f"[AUTH DEBUG] has_permission 成功: 'read' 权限")
                return is_safe # 'read' 权限只允许安全操作
        
        # --- 检查 3: TripViewSet (retrieve/update) ---
        if 'trip_id' not in view.kwargs:
            # 'list' 已被 "is_authenticated" 检查处理。
            # 'retrieve' (等) 必须传递给 has_object_permission。
            print(f"[AUTH DEBUG] has_permission: 允许进入 has_object_permission")
            return True 
        
        # --- 最终失败 ---
        print(f"[AUTH DEBUG] has_permission 失败: 既不是所有者，也无有效 ShareLink。")
        return False


    def has_object_permission(self, request, view, obj):
        print("--- [AUTH DEBUG] 运行 has_object_permission ---")
        
        trip = None
        if isinstance(obj, Trip):
            trip = obj
        elif hasattr(obj, 'trip'):
            trip = obj.trip
        elif hasattr(obj, 'day'):
            trip = obj.day.trip
        
        if not trip:
            print("[AUTH DEBUG] has_object_permission 失败: 未能从 'obj' 中找到 trip 对象")
            return False

        # --- 检查 1: 已登录用户 (所有者检查) ---
        if request.user and request.user.is_authenticated:
            if trip.user == request.user:
                print("[AUTH DEBUG] has_object_permission 成功: 检查所有者: True")
                return True # 是所有者，允许

            # 用户已登录，但不是所有者。继续检查 ShareLink。
            print("[AUTH DEBUG] has_object_permission 检查所有者: False. 继续检查 ShareLink...")

        # --- 检查 2: 分享链接用户 ---
        if request.auth and isinstance(request.auth, ShareLink):
            share_link = request.auth
            print(f"[AUTH DEBUG] has_object_permission 检查 ShareLink: Token (Trip {share_link.trip.pk}) vs URL (Trip {trip.pk})")
            
            if share_link.trip.pk == trip.pk:
                if share_link.permission_level == 'edit':
                    print("[AUTH DEBUG] has_object_permission 成功: 'edit' 权限")
                    return True 
                if share_link.permission_level == 'read':
                    is_safe = request.method in permissions.SAFE_METHODS
                    print(f"[AUTH DEBUG] has_object_permission 检查 'read' 权限: 方法 {request.method} 是否安全? {is_safe}")
                    return is_safe
            else:
                print("[AUTH DEBUG] has_object_permission 失败: ShareLink Token 与目标 Trip 对象不匹配")
        
        # --- 最终失败 ---
        print(f"[AUTH DEBUG] has_object_permission 失败: 既不是所有者，也无有效 ShareLink。")
        return False