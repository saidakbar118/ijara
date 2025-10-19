from django.shortcuts import render, redirect, get_object_or_404
from django.db.models import Q, Sum, Count
from django.utils import timezone
from django.core.paginator import Paginator
from django.http import JsonResponse
from .models import *
from .forms import *

def dashboard(request):
    # Statistika
    total_tools = Tool.objects.count()
    available_tools = Tool.objects.aggregate(Sum('quantity_available'))['quantity_available__sum'] or 0
    total_quantity = Tool.objects.aggregate(Sum('quantity_total'))['quantity_total__sum'] or 0
    rented_tools = total_quantity - available_tools
    
    active_rentals = Rental.objects.filter(status='active').count()
    
    # Oxirgi 5 ta ijara
    recent_rentals = Rental.objects.all().order_by('-created_at')[:5]
    
    # Bugungi daromad
    today_income = Rental.objects.filter(
        created_at__date=timezone.now().date(),
        status='active'
    ).aggregate(Sum('total_amount'))['total_amount__sum'] or 0
    
    # Mashhur asboblar
    popular_tools = Tool.objects.annotate(
        rental_count=Count('rentalitem')
    ).order_by('-rental_count')[:4]
    
    context = {
        'total_tools': total_tools,
        'available_tools': available_tools,
        'rented_tools': rented_tools,
        'active_rentals': active_rentals,
        'recent_rentals': recent_rentals,
        'today_income': today_income,
        'popular_tools': popular_tools,
    }
    return render(request, 'main/dashboard.html', context)

def rental_list(request):
    rentals = Rental.objects.all().order_by('-created_at')
    
    # Qidiruv
    query = request.GET.get('q', '')
    status_filter = request.GET.get('status', '')
    
    if query:
        rentals = rentals.filter(
            Q(customer__name__icontains=query) |
            Q(customer__phone__icontains=query) |
            Q(rentalitem__tool__name__icontains=query)
        ).distinct()
    
    if status_filter:
        rentals = rentals.filter(status=status_filter)
    
    # Kunlar sonini hisoblash
    for rental in rentals:
        rental.current_days = rental.get_total_days()
    
    paginator = Paginator(rentals, 10)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    context = {
        'page_obj': page_obj,
        'query': query,
        'status_filter': status_filter,
    }
    return render(request, 'main/rental_list.html', context)

def rental_detail(request, rental_id):
    rental = get_object_or_404(Rental, id=rental_id)
    rental_items = rental.rentalitem_set.all()
    
    context = {
        'rental': rental,
        'rental_items': rental_items,
    }
    return render(request, 'main/rental_detail.html', context)

def create_rental(request):
    if request.method == 'POST':
        form = RentalForm(request.POST)
        if form.is_valid():
            rental = form.save()
            return redirect(f'/rentals/{rental.id}/items/')
    else:
        form = RentalForm(initial={'start_date': timezone.now().date()})
    
    context = {
        'form': form,
        'title': 'Yangi Ijara'
    }
    return render(request, 'main/create_rental.html', context)

def add_rental_items(request, rental_id):
    rental = get_object_or_404(Rental, id=rental_id)
    tools = Tool.objects.filter(quantity_available__gt=0, is_active=True)
    
    if request.method == 'POST':
        if 'add_item' in request.POST:
            tool_id = request.POST.get('tool')
            quantity = int(request.POST.get('quantity', 0))
            
            tool = get_object_or_404(Tool, id=tool_id)
            
            if quantity > 0 and quantity <= tool.quantity_available:
                rental_item, created = RentalItem.objects.get_or_create(
                    rental=rental,
                    tool=tool,
                    defaults={
                        'quantity': quantity,
                        'daily_rate': tool.daily_price
                    }
                )
                
                if not created:
                    rental_item.quantity += quantity
                    rental_item.save()
                
                tool.quantity_available -= quantity
                tool.save()
                rental.calculate_total()
        
        elif 'remove_item' in request.POST:
            item_id = request.POST.get('item_id')
            rental_item = get_object_or_404(RentalItem, id=item_id, rental=rental)
            
            tool = rental_item.tool
            tool.quantity_available += rental_item.quantity
            tool.save()
            
            rental_item.delete()
            rental.calculate_total()
        
        elif 'complete_rental' in request.POST:
            rental.end_date = timezone.now().date()
            rental.status = 'completed'
            rental.save()
            return redirect('rental_detail', rental_id=rental.id)
    
    rental_items = rental.rentalitem_set.all()
    
    context = {
        'rental': rental,
        'tools': tools,
        'rental_items': rental_items,
    }
    return render(request, 'main/add_rental_items.html', context)

def complete_rental(request, rental_id):
    rental = get_object_or_404(Rental, id=rental_id)
    
    if request.method == 'POST':
        rental.end_date = timezone.now().date()
        rental.status = 'completed'
        rental.save()
        
        # Asboblarni qaytarish
        rental_items = rental.rentalitem_set.all()
        for item in rental_items:
            tool = item.tool
            tool.quantity_available += item.quantity
            tool.save()
    
    return redirect(f'/rentals/{rental.id}/')

def tool_list(request):
    tools = Tool.objects.all()
    context = {
        'tools': tools,
        'title': 'Asboblar Ro\'yxati'
    }
    return render(request, 'main/tool_list.html', context)

def create_tool(request):
    if request.method == 'POST':
        form = ToolForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('/tools/')
    else:
        form = ToolForm()
    
    context = {
        'form': form,
        'title': 'Yangi Asbob'
    }
    return render(request, 'main/create_tool.html', context)

def customer_list(request):
    customers = Customer.objects.all()
    context = {
        'customers': customers,
        'title': 'Mijozlar Ro\'yxati'
    }
    return render(request, 'main/customer_list.html', context)

def create_customer(request):
    if request.method == 'POST':
        form = CustomerForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('/customers/')
    else:
        form = CustomerForm()
    
    context = {
        'form': form,
        'title': 'Yangi Mijoz'
    }
    return render(request, 'main/create_customer.html', context)

def get_dashboard_stats(request):
    """AJAX uchun dashboard statistikasi"""
    total_tools = Tool.objects.count()
    available_tools = Tool.objects.aggregate(Sum('quantity_available'))['quantity_available__sum'] or 0
    total_quantity = Tool.objects.aggregate(Sum('quantity_total'))['quantity_total__sum'] or 0
    rented_tools = total_quantity - available_tools
    active_rentals = Rental.objects.filter(status='active').count()
    
    return JsonResponse({
        'total_tools': total_tools,
        'available_tools': available_tools,
        'rented_tools': rented_tools,
        'active_rentals': active_rentals,
    })