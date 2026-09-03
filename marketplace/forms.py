from django import forms
from .models import Item

class ItemForm(forms.ModelForm):
    class Meta:
        model = Item
        fields = ['title', 'description', 'listing_type', 'price', 'rent_price_per_day', 'condition', 'category', 'image']
        widgets = {
            'listing_type': forms.Select(attrs={'class': 'form-select'}),
            'price': forms.NumberInput(attrs={'placeholder': '₹ One-time buy price (if selling)', 'min': '0'}),
            'rent_price_per_day': forms.NumberInput(attrs={'placeholder': '₹ / day (if renting)', 'min': '0'}),
        }
