from django.shortcuts import render, redirect, get_object_or_404
from django.db.models import Q, Sum, Count
from django.utils import timezone
from django.core.paginator import Paginator
from django.http import JsonResponse
from .models import *
from .forms import *
# views.py
from django.db.models import Count, Sum



def dashboard(request):
    # Asosiy statistika
    total_tools = Tool.objects.count()
    available_tools = Tool.objects.aggregate(Sum('quantity_available'))['quantity_available__sum'] or 0
    total_quantity = Tool.objects.aggregate(Sum('quantity_total'))['quantity_total__sum'] or 0
    rented_tools = total_quantity - available_tools
    
    active_rentals = Rental.objects.filter(status='active').count()
    
    # Asboblar statistikasi - TO'G'RI HISOBLASH
    tools_stats = []
    total_total = 0
    
    for tool in Tool.objects.all():
        # Faol ijaralardagi asbob sonini hisoblash
        rented_count = RentalItem.objects.filter(
            tool=tool, 
            rental__status='active'
        ).aggregate(total=Sum('quantity'))['total'] or 0
        
        tools_stats.append({
            'name': tool.name,
            'quantity_total': tool.quantity_total,
            'quantity_available': tool.quantity_available,
            'rented_count': rented_count
        })
        total_total += tool.quantity_total
    
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
        'tools_stats': tools_stats,
        'total_tools_stats': {
            'total_total': total_total
        }
    }
    return render(request, 'main/dashboard.html', context)


# views.py ga yangi view qo'shamiz
from django.contrib.auth import logout
from django.shortcuts import redirect

def custom_logout(request):
    logout(request)
    return redirect('/login/')

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


# views.py
from django.utils import timezone
from datetime import date, datetime

def create_rental(request):
    if request.method == 'POST':
        form = RentalForm(request.POST)
        if form.is_valid():
            rental = form.save(commit=False)
            # Sanani tekshirish
            if not rental.start_date:
                rental.start_date = timezone.now().date()
            rental.save()
            return redirect('main:add_rental_items', rental_id=rental.id)
    else:
        # Boshlang'ich sana - bugun
        today = timezone.now().date()
        form = RentalForm(initial={'start_date': today})
    
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
            quantity = int(request.POST.get('quantity', 1))  # default 1
            
            tool = get_object_or_404(Tool, id=tool_id)
            
            if quantity > 0 and quantity <= tool.quantity_available:
                # Asbobni qo'shish
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
                
                # Summani yangilash
                rental.calculate_total()
                
                messages.success(request, f"'{tool.name}' asbobi qo'shildi.")
            else:
                messages.error(request, f"Noto'g'ri son. Mavjud: {tool.quantity_available}")
            
            return redirect('main:add_rental_items', rental_id=rental.id)
        
        elif 'remove_item' in request.POST:
            item_id = request.POST.get('item_id')
            rental_item = get_object_or_404(RentalItem, id=item_id, rental=rental)
            tool_name = rental_item.tool.name
            
            # Asbobni qaytarish
            tool = rental_item.tool
            tool.quantity_available += rental_item.quantity
            tool.save()
            
            rental_item.delete()
            # Summa avtomatik yangilanadi (modeldagi delete)
            
            messages.success(request, f"'{tool_name}' asbobi olib tashlandi.")
            return redirect('main:add_rental_items', rental_id=rental.id)
        
        elif 'complete_rental' in request.POST:
            # Ijarani yakunlash
            rental.end_date = timezone.now().date()
            rental.status = 'completed'
            rental.save()
            rental.calculate_total()
            
            messages.success(request, "Ijara yakunlandi!")
            return redirect('main:rental_detail', rental_id=rental.id)
    
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
    
    
    
# views.py
from django.contrib import messages

# Asbobni o'chirish
def delete_tool(request, tool_id):
    tool = get_object_or_404(Tool, id=tool_id)
    if request.method == 'POST':
        # Asbob faol ijaralarda ishlatilayotganligini tekshirish
        active_rentals = RentalItem.objects.filter(tool=tool, rental__status='active')
        if active_rentals.exists():
            messages.error(request, f"'{tool.name}' asbobi faol ijaralarda ishlatilmoqda. Oldin ijaralarni yakunlang.")
            return redirect('main:tool_list')
        
        tool.delete()
        messages.success(request, f"'{tool.name}' asbobi o'chirildi.")
    return redirect('main:tool_list')

# Asbobni tahrirlash
def edit_tool(request, tool_id):
    tool = get_object_or_404(Tool, id=tool_id)
    if request.method == 'POST':
        form = ToolForm(request.POST, instance=tool)
        if form.is_valid():
            form.save()
            messages.success(request, f"'{tool.name}' asbobi yangilandi.")
            return redirect('main:tool_list')
    else:
        form = ToolForm(instance=tool)
    
    context = {
        'form': form,
        'title': 'Asbobni Tahrirlash',
        'tool': tool,
    }
    return render(request, 'main/edit_tool.html', context)
# edit_rental funksiyasini yangilaymiz
def edit_rental(request, rental_id):
    rental = get_object_or_404(Rental, id=rental_id)
    
    if request.method == 'POST':
        form = RentalForm(request.POST, instance=rental)
        if form.is_valid():
            # Faqat boshlanish sanasini yangilash
            old_start_date = rental.start_date
            rental = form.save()
            
            # Agar sana o'zgarsa, summani qayta hisoblash
            if old_start_date != rental.start_date:
                rental.calculate_total()
            
            messages.success(request, "Ijara yangilandi.")
            return redirect('main:rental_detail', rental_id=rental.id)
    else:
        form = RentalForm(instance=rental)
    
    context = {
        'form': form,
        'title': 'Ijarani Tahrirlash',
        'rental': rental,
    }
    return render(request, 'main/edit_rental.html', context)

# edit_customer funksiyasini yangilaymiz
def edit_customer(request, customer_id):
    customer = get_object_or_404(Customer, id=customer_id)
    
    if request.method == 'POST':
        form = CustomerForm(request.POST, instance=customer)
        if form.is_valid():
            form.save()
            messages.success(request, f"'{customer.name}' mijoz yangilandi.")
            return redirect('main:customer_list')
    else:
        form = CustomerForm(instance=customer)
    
    # Mijoz statistikasini hisoblash
    total_rentals = customer.rental_set.count()
    active_rentals = customer.rental_set.filter(status='active').count()
    
    context = {
        'form': form,
        'title': 'Mijozni Tahrirlash',
        'customer': customer,
        'total_rentals': total_rentals,
        'active_rentals': active_rentals,
    }
    return render(request, 'main/edit_customer.html', context)
# Mijozni o'chirish
def delete_customer(request, customer_id):
    customer = get_object_or_404(Customer, id=customer_id)
    if request.method == 'POST':
        # Mijozning faol ijaralarini tekshirish
        active_rentals = customer.rental_set.filter(status='active')
        if active_rentals.exists():
            messages.error(request, f"'{customer.name}' mijozning faol ijaralari mavjud. Oldin ijaralarni yakunlang.")
            return redirect('main:customer_list')
        
        customer.delete()
        messages.success(request, f"'{customer.name}' mijoz o'chirildi.")
    return redirect('main:customer_list')

#
# Ijarani o'chirish
def delete_rental(request, rental_id):
    rental = get_object_or_404(Rental, id=rental_id)
    if request.method == 'POST':
        if rental.status == 'active':
            # Asboblarni qaytarish
            rental_items = rental.rentalitem_set.all()
            for item in rental_items:
                tool = item.tool
                tool.quantity_available += item.quantity
                tool.save()
        
        rental.delete()
        messages.success(request, f"Ijara o'chirildi.")
    return redirect('main:rental_list')
