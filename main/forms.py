from django import forms
from .models import Tool, Customer, Rental, RentalItem, ToolCategory

class ToolForm(forms.ModelForm):
    class Meta:
        model = Tool
        fields = ['name', 'category', 'daily_price', 'quantity_total']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Asbob nomi'}),
            'category': forms.Select(attrs={'class': 'form-control'}),
            'daily_price': forms.NumberInput(attrs={'class': 'form-control', 'placeholder': 'Kunlik narx', 'step': '1000'}),
            'quantity_total': forms.NumberInput(attrs={'class': 'form-control', 'placeholder': 'Jami soni'}),
        }
        labels = {
            'name': 'Asbob nomi',
            'category': 'Kategoriya',
            'daily_price': 'Kunlik narx (soʻm)',
            'quantity_total': 'Jami soni',
        }

class CustomerForm(forms.ModelForm):
    class Meta:
        model = Customer
        fields = ['name', 'phone', 'address']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Mijoz ismi'}),
            'phone': forms.TextInput(attrs={'class': 'form-control', 'placeholder': '+998901234567'}),
            'address': forms.Textarea(attrs={'class': 'form-control', 'placeholder': 'Manzil', 'rows': 3}),
        }
        labels = {
            'name': 'Ism',
            'phone': 'Telefon',
            'address': 'Manzil',
        }

class RentalForm(forms.ModelForm):
    class Meta:
        model = Rental
        fields = ['customer', 'start_date']
        widgets = {
            'customer': forms.Select(attrs={'class': 'form-control'}),
            'start_date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
        }
        labels = {
            'customer': 'Mijoz',
            'start_date': 'Boshlanish sanasi',
        }

class RentalItemForm(forms.ModelForm):
    class Meta:
        model = RentalItem
        fields = ['tool', 'quantity']
        widgets = {
            'tool': forms.Select(attrs={'class': 'form-control'}),
            'quantity': forms.NumberInput(attrs={'class': 'form-control', 'min': 1}),
        }