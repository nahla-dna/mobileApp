# admin.py - Advanced Django Admin Techniques

from django.contrib import admin
from django.contrib.auth.models import User
from django.db.models import Q, Count, Sum, Avg
from django.utils.html import format_html
from django.urls import path, reverse
from django.shortcuts import render
from django.http import HttpResponse
from django.utils import timezone
from datetime import timedelta
import csv

from .models import Author, Book, Category, Member, Borrowing


# ============================================
# 1. CUSTOM FILTERS
# ============================================

class PriceRangeFilter(admin.SimpleListFilter):
    """
    Custom filter for price ranges
    """
    title = 'price range'
    parameter_name = 'price'

    def lookups(self, request, model_admin):
        """Define filter options"""
        return (
            ('cheap', 'Under $10'),
            ('medium', '$10 - $30'),
            ('expensive', 'Over $30'),
        )

    def queryset(self, request, queryset):
        """Filter the queryset based on selection"""
        if self.value() == 'cheap':
            return queryset.filter(price__lt=10)
        if self.value() == 'medium':
            return queryset.filter(price__gte=10, price__lte=30)
        if self.value() == 'expensive':
            return queryset.filter(price__gt=30)
        return queryset


class AvailabilityFilter(admin.SimpleListFilter):
    """
    Filter books by availability
    """
    title = 'availability'
    parameter_name = 'available'

    def lookups(self, request, model_admin):
        return (
            ('available', 'Available'),
            ('unavailable', 'Out of Stock'),
            ('low', 'Low Stock (< 5)'),
        )

    def queryset(self, request, queryset):
        if self.value() == 'available':
            return queryset.filter(available_copies__gt=0)
        if self.value() == 'unavailable':
            return queryset.filter(available_copies=0)
        if self.value() == 'low':
            return queryset.filter(available_copies__gt=0, available_copies__lt=5)
        return queryset


class YearPublishedFilter(admin.SimpleListFilter):
    """
    Filter by publication year
    """
    title = 'publication year'
    parameter_name = 'year'

    def lookups(self, request, model_admin):
        years = Book.objects.dates('published_date', 'year', order='DESC')
        return [(year.year, year.year) for year in years]

    def queryset(self, request, queryset):
        if self.value():
            return queryset.filter(published_date__year=self.value())
        return queryset


class OverdueBorrowingFilter(admin.SimpleListFilter):
    """
    Filter overdue borrowings
    """
    title = 'overdue status'
    parameter_name = 'overdue'

    def lookups(self, request, model_admin):
        return (
            ('overdue', 'Overdue'),
            ('due_soon', 'Due within 3 days'),
            ('on_time', 'On Time'),
        )

    def queryset(self, request, queryset):
        today = timezone.now().date()
        if self.value() == 'overdue':
            return queryset.filter(returned=False, due_date__lt=today)
        if self.value() == 'due_soon':
            soon = today + timedelta(days=3)
            return queryset.filter(returned=False, due_date__lte=soon, due_date__gte=today)
        if self.value() == 'on_time':
            return queryset.filter(returned=False, due_date__gte=today)
        return queryset


# ============================================
# 2. CUSTOM PERMISSIONS & ACCESS CONTROL
# ============================================

class RestrictedBookAdmin(admin.ModelAdmin):
    """
    Book admin with custom permissions
    """
    list_display = ['title', 'author', 'price', 'available_copies', 'user_can_edit']
    list_filter = [PriceRangeFilter, AvailabilityFilter, YearPublishedFilter]
    search_fields = ['title', 'isbn', 'author__name']

    def get_queryset(self, request):
        """
        Modify queryset based on user permissions
        """
        qs = super().get_queryset(request)
        
        # If user is not superuser, show only books they can manage
        if not request.user.is_superuser:
            # Example: Show only books from certain categories
            return qs.filter(categories__name__in=['Fiction', 'Non-Fiction'])
        
        return qs

    def has_add_permission(self, request):
        """
        Control who can add books
        """
        # Only staff with specific permission can add
        return request.user.has_perm('library.add_book')

    def has_change_permission(self, request, obj=None):
        """
        Control who can edit books
        """
        # Superusers can edit everything
        if request.user.is_superuser:
            return True
        
        # Others can only edit if book price is below $50
        if obj and obj.price > 50:
            return False
        
        return request.user.has_perm('library.change_book')

    def has_delete_permission(self, request, obj=None):
        """
        Control who can delete books
        """
        # Only superusers can delete
        return request.user.is_superuser

    def has_view_permission(self, request, obj=None):
        """
        Control who can view books (Django 2.1+)
        """
        return request.user.has_perm('library.view_book')

    @admin.display(description='Can Edit', boolean=True)
    def user_can_edit(self, obj):
        """Display if current user can edit this book"""
        from django.contrib.admin.views.main import REQUEST_VAR
        # This is a simplified version - in real use, you'd need request context
        return obj.price <= 50

    def save_model(self, request, obj, form, change):
        """
        Custom save logic - track who created/modified
        """
        if not change:  # New object
            obj.created_by = request.user
        obj.modified_by = request.user
        super().save_model(request, obj, form, change)

    def get_readonly_fields(self, request, obj=None):
        """
        Make fields readonly based on user permissions
        """
        if not request.user.is_superuser:
            return ['price', 'isbn']  # Regular users can't edit these
        return []


# ============================================
# 3. CUSTOM ADMIN ACTIONS WITH PERMISSIONS
# ============================================

@admin.register(Book)
class BookAdmin(admin.ModelAdmin):
    list_display = ['title', 'author', 'price', 'available_copies', 'status_badge']
    list_filter = [PriceRangeFilter, AvailabilityFilter, YearPublishedFilter]
    search_fields = ['title', 'isbn', 'author__name']
    actions = [
        'export_to_csv',
        'mark_unavailable',
        'apply_discount',
        'send_notification'
    ]

    @admin.display(description='Status')
    def status_badge(self, obj):
        if obj.available_copies == 0:
            color = 'red'
            text = 'Out of Stock'
        elif obj.available_copies < 5:
            color = 'orange'
            text = 'Low Stock'
        else:
            color = 'green'
            text = 'In Stock'
        return format_html(
            '<span style="background: {}; color: white; padding: 3px 10px; '
            'border-radius: 3px; font-size: 11px;">{}</span>',
            color, text
        )

    @admin.action(description='Export selected to CSV', permissions=['view'])
    def export_to_csv(self, request, queryset):
        """
        Export selected books to CSV
        permissions=['view'] means user needs view permission
        """
        response = HttpResponse(content_type='text/csv')
        response['Content-Disposition'] = 'attachment; filename="books.csv"'
        
        writer = csv.writer(response)
        writer.writerow(['Title', 'Author', 'ISBN', 'Price', 'Available Copies'])
        
        for book in queryset:
            writer.writerow([
                book.title,
                book.author.name,
                book.isbn,
                book.price,
                book.available_copies
            ])
        
        return response

    @admin.action(description='Mark as unavailable', permissions=['change'])
    def mark_unavailable(self, request, queryset):
        """
        Requires change permission
        """
        updated = queryset.update(available_copies=0)
        self.message_user(
            request,
            f'{updated} book(s) marked as unavailable.',
            level='warning'
        )

    @admin.action(description='Apply 20% discount', permissions=['change'])
    def apply_discount(self, request, queryset):
        """
        Custom action with permission check
        """
        if not request.user.has_perm('library.can_apply_discount'):
            self.message_user(
                request,
                'You do not have permission to apply discounts.',
                level='error'
            )
            return

        count = 0
        for book in queryset:
            book.price = book.price * 0.8
            book.save()
            count += 1
        
        self.message_user(
            request,
            f'20% discount applied to {count} book(s).',
            level='success'
        )

    def has_export_to_csv_permission(self, request):
        """Custom permission check for export action"""
        return request.user.has_perm('library.view_book')

    def has_mark_unavailable_permission(self, request):
        """Custom permission check for mark unavailable action"""
        return request.user.has_perm('library.change_book')

    def has_apply_discount_permission(self, request):
        """Custom permission check for discount action"""
        return request.user.is_superuser


# ============================================
# 4. CUSTOM ADMIN DASHBOARD
# ============================================

class LibraryAdminSite(admin.AdminSite):
    """
    Custom Admin Site with dashboard
    """
    site_header = 'Library Management System'
    site_title = 'Library Admin'
    index_title = 'Dashboard'

    def get_urls(self):
        """Add custom URLs to admin"""
        urls = super().get_urls()
        custom_urls = [
            path('dashboard/', self.admin_view(self.dashboard_view), name='dashboard'),
            path('reports/', self.admin_view(self.reports_view), name='reports'),
        ]
        return custom_urls + urls

    def dashboard_view(self, request):
        """
        Custom dashboard with statistics
        """
        # Gather statistics
        context = {
            **self.each_context(request),
            'total_books': Book.objects.count(),
            'available_books': Book.objects.filter(available_copies__gt=0).count(),
            'total_members': Member.objects.count(),
            'active_members': Member.objects.filter(is_active=True).count(),
            'active_borrowings': Borrowing.objects.filter(returned=False).count(),
            'overdue_borrowings': Borrowing.objects.filter(
                returned=False,
                due_date__lt=timezone.now().date()
            ).count(),
            'total_authors': Author.objects.count(),
            'total_categories': Category.objects.count(),
            
            # Advanced statistics
            'most_borrowed_books': Book.objects.annotate(
                borrow_count=Count('borrowings')
            ).order_by('-borrow_count')[:5],
            
            'top_members': Member.objects.annotate(
                borrow_count=Count('borrowings')
            ).order_by('-borrow_count')[:5],
            
            'recent_borrowings': Borrowing.objects.select_related(
                'member', 'book'
            ).order_by('-borrow_date')[:10],
            
            'overdue_list': Borrowing.objects.filter(
                returned=False,
                due_date__lt=timezone.now().date()
            ).select_related('member', 'book')[:10],
            
            # Financial stats
            'total_inventory_value': Book.objects.aggregate(
                total=Sum('price')
            )['total'] or 0,
            
            'average_book_price': Book.objects.aggregate(
                avg=Avg('price')
            )['avg'] or 0,
        }
        
        return render(request, 'admin/library_dashboard.html', context)

    def reports_view(self, request):
        """
        Custom reports page
        """
        context = {
            **self.each_context(request),
            'title': 'Library Reports',
        }
        return render(request, 'admin/library_reports.html', context)


# Create custom admin site instance
library_admin_site = LibraryAdminSite(name='library_admin')

# Register models with custom admin site
library_admin_site.register(Book, BookAdmin)
library_admin_site.register(Author)
library_admin_site.register(Category)
library_admin_site.register(Member)
library_admin_site.register(Borrowing)


# ============================================
# 5. INLINE ADMIN WITH PERMISSIONS
# ============================================

class BorrowingInline(admin.TabularInline):
    model = Borrowing
    extra = 0
    readonly_fields = ['borrow_date', 'overdue_status']
    fields = ['book', 'borrow_date', 'due_date', 'returned', 'overdue_status']

    def overdue_status(self, obj):
        if obj.is_overdue():
            return format_html('<span style="color: red;">⚠ OVERDUE</span>')
        return format_html('<span style="color: green;">✓ On Time</span>')
    overdue_status.short_description = 'Status'

    def has_add_permission(self, request, obj=None):
        """Control who can add borrowings inline"""
        return request.user.has_perm('library.add_borrowing')

    def has_delete_permission(self, request, obj=None):
        """Prevent deletion of borrowings"""
        return False


@admin.register(Member)
class MemberAdminWithInline(admin.ModelAdmin):
    list_display = ['name', 'email', 'is_active', 'total_borrowings', 'active_count']
    inlines = [BorrowingInline]
    
    def total_borrowings(self, obj):
        return obj.borrowings.count()
    total_borrowings.short_description = 'Total Borrowed'
    
    def active_count(self, obj):
        count = obj.borrowings.filter(returned=False).count()
        if count > 5:
            return format_html('<span style="color: red;">{}</span>', count)
        return count
    active_count.short_description = 'Currently Borrowed'


# ============================================
# 6. CUSTOM MODEL PERMISSIONS (in models.py)
# ============================================

"""
Add to your Book model:

class Book(models.Model):
    # ... fields ...
    
    class Meta:
        permissions = [
            ("can_apply_discount", "Can apply discount to books"),
            ("can_view_reports", "Can view library reports"),
            ("can_manage_inventory", "Can manage book inventory"),
        ]
"""


# ============================================
# 7. USAGE IN urls.py
# ============================================

"""
# In your urls.py:

from django.contrib import admin
from django.urls import path
from myapp.admin import library_admin_site

urlpatterns = [
    path('admin/', admin.site.urls),  # Default admin
    path('library-admin/', library_admin_site.urls),  # Custom admin
]
"""