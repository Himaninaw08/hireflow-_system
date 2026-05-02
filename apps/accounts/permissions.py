from rest_framework import permissions

class IsEmployer(permissions.BasePermission):
    def has_permission(self, request, view):
        return request.user and request.user.is_authenticated and request.user.role == 'employer'

class IsCandidate(permissions.BasePermission):
    def has_permission(self, request, view):
        return request.user and request.user.is_authenticated and request.user.role == 'candidate'

class IsRecruiter(permissions.BasePermission):
    def has_permission(self, request, view):
        return request.user and request.user.is_authenticated and request.user.role in ['employer', 'recruiter']

class IsAdmin(permissions.BasePermission):
    def has_permission(self, request, view):
        return request.user and request.user.is_authenticated and request.user.role == 'admin'

class IsOwnerOrReadOnly(permissions.BasePermission):
    def has_object_permission(self, request, view, obj):
        if request.method in permissions.SAFE_METHODS:
            return True
        
        if hasattr(obj, 'user'):
            return obj.user == request.user
        elif hasattr(obj, 'created_by'):
            return obj.created_by == request.user
        elif hasattr(obj, 'candidate'):
            return obj.candidate == request.user
        elif hasattr(obj, 'owner'):
            return obj.owner == request.user
        
        return obj == request.user

class IsCompanyMember(permissions.BasePermission):
    def has_permission(self, request, view):
        return request.user and request.user.is_authenticated and request.user.role in ['employer', 'recruiter', 'admin']
    
    def has_object_permission(self, request, view, obj):
        if hasattr(obj, 'company'):
            company = obj.company
        elif hasattr(obj, 'job') and hasattr(obj.job, 'company'):
            company = obj.job.company
        else:
            return False
        
        return company.members.filter(user=request.user).exists() or company.owner == request.user
