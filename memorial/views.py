import re
import unicodedata
from django.core.paginator import Paginator
from django.db.models import Q
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, render
from .models import Martyr

def normalize(value):
    value = value.replace("đ", "d").replace("Đ", "D")
    return re.sub(r"\s+", " ", "".join(c for c in unicodedata.normalize("NFD", value) if unicodedata.category(c) != "Mn")).lower().strip()

def home(request):
    query = request.GET.get("q", "").strip()
    zone = request.GET.get("zone", "").strip()
    records = Martyr.objects.all()
    if query:
        normalized = normalize(query)
        records = records.filter(Q(normalized_name__icontains=normalized) | Q(hometown__icontains=query) | Q(grave_number__iexact=query))
    if zone:
        records = records.filter(zone=zone)
    page = Paginator(records, 24).get_page(request.GET.get("page"))
    zones = Martyr.objects.exclude(zone="").values_list("zone", flat=True).distinct().order_by("zone")
    return render(request, "memorial/home.html", {"page": page, "query": query, "zone": zone, "zones": zones, "total": Martyr.objects.count()})

def detail(request, source_id):
    return render(request, "memorial/detail.html", {"martyr": get_object_or_404(Martyr, source_id=source_id)})

def tour(request):
    return render(request, "memorial/tour.html")

def health(request):
    return JsonResponse({"status": "ok"})

