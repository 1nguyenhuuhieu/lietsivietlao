import re
import unicodedata
import hashlib
import random
import time
import os
import json
import mimetypes
from io import BytesIO
from pathlib import Path
from datetime import timedelta
from PIL import Image, ImageOps, UnidentifiedImageError
from django.conf import settings
from django.contrib import messages
from django.contrib.auth.decorators import user_passes_test
from django.contrib.admin.views.decorators import staff_member_required
from django.core import signing
from django.core.paginator import Paginator
from django.db.models import Case, IntegerField, Q, Value, When
from django.http import FileResponse, HttpResponse, JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_POST, require_http_methods
from django.utils import timezone
from .forms import FamilyConnectionForm, TributeForm
from .models import FamilySubmission, Martyr, Tribute, TourConfiguration, TourPoint

HOME_IMAGE_SLOTS = {
    "hero": ("hero", 2400, "#173c2b"),
    "tour": ("tour", 2200, "#173c2b"),
    "about_gate": ("cau-chuyen-home", 2000, "#f4f0e6"),
    "about_graves": ("cau-chuyen-home", 1600, "#f4f0e6"),
    "stele_vi": ("cau-chuyen-home", 1400, "#f4f0e6"),
    "stele_lo": ("cau-chuyen-home", 1400, "#f4f0e6"),
}

HOME_IMAGE_FALLBACKS = {
    "hero": "/static/images/hero-cong-tuong-niem-v3.png",
    "tour": "/static/images/nghia-trang-viet-lao-panorama-360.jpg",
    "about_gate": "/static/images/about/cong-nghia-trang.jpg",
    "about_graves": "/static/images/about/cac-anh-nam-giua-long-dat-me.jpg",
    "stele_vi": "/static/images/about/bia-song-ngu-viet-lao-1.png",
    "stele_lo": "/static/images/about/bia-song-ngu-viet-lao-2.png",
}


def _home_image_urls():
    upload_dir = Path(settings.STATIC_ROOT) / "uploads" / "home"
    urls = {}
    for key, fallback in HOME_IMAGE_FALLBACKS.items():
        image_path = upload_dir / f"{key}.webp"
        urls[key] = f"/static/uploads/home/{key}.webp?v={image_path.stat().st_mtime_ns}" if image_path.exists() else fallback
    return urls

def normalize(value):
    value = value.replace("đ", "d").replace("Đ", "D")
    return re.sub(r"\s+", " ", "".join(c for c in unicodedata.normalize("NFD", value) if unicodedata.category(c) != "Mn")).lower().strip()

def generated_memorial_messages(martyr):
    """Deterministic editorial memorials, clearly labelled as system text."""
    openings = [
        "Xin nghiêng mình tưởng nhớ", "Đời đời ghi nhớ công ơn", "Thành kính tri ân",
        "Một nén tâm hương kính dâng", "Tổ quốc và nhân dân mãi khắc ghi",
        "Trong lòng đất Mẹ, xin được tưởng nhớ", "Bằng tất cả lòng biết ơn, xin tri ân",
        "Kính cẩn tưởng niệm", "Xin thắp một nén hương lòng tưởng nhớ",
        "Các thế hệ hôm nay mãi biết ơn", "Tên tuổi và sự hy sinh của đồng chí sẽ còn mãi",
        "Trước anh linh người đã khuất, xin thành kính tri ân",
    ]
    legacies = [
        "người đã hiến dâng tuổi xuân cho độc lập, tự do của hai dân tộc Việt Nam – Lào.",
        "người con đã nằm lại vì nghĩa tình quốc tế cao đẹp và bình yên của Tổ quốc.",
        "sự hy sinh cao cả đã góp phần vun đắp tình hữu nghị Việt – Lào đời đời bền vững.",
        "người chiến sĩ đã đi trọn lời thề với non sông và nhân dân.",
        "một cuộc đời đã hóa thành ký ức bất tử trong lòng các thế hệ mai sau.",
        "người đã gửi lại tuổi xuân nơi chiến trường vì hòa bình hôm nay.",
        "một người con của đất Việt đã sống, chiến đấu và hy sinh đầy quả cảm.",
        "người đã góp phần làm nên những năm tháng không thể nào quên của hai dân tộc.",
        "một sự hy sinh thầm lặng nhưng không bao giờ bị lãng quên.",
        "người anh hùng đã nằm xuống để đất nước được nở hoa độc lập.",
        "một phần máu xương của Tổ quốc đang yên nghỉ giữa lòng quê hương.",
        "người đã chọn hy sinh để những thế hệ sau được sống trong hòa bình.",
    ]
    closings = [
        "Xin người an nghỉ.", "Danh thơm còn mãi với non sông.",
        "Đời đời nhớ ơn các anh hùng liệt sĩ.", "Ký ức về người sẽ mãi được gìn giữ.",
        "Tình đất nước và nghĩa đồng bào mãi ở bên người.",
        "Xin gửi nơi đây lòng biết ơn sâu sắc nhất.", "Ngọn lửa tri ân sẽ còn được trao truyền mãi mãi.",
        "Sự hy sinh ấy sẽ mãi soi sáng các thế hệ mai sau.",
    ]
    rng = random.Random(f"viet-lao-{martyr.source_id}")
    combinations = [(a, b, c) for a in openings for b in legacies for c in closings]
    return [" ".join(parts) for parts in rng.sample(combinations, 3)]

def _filtered_records(request):
    query = request.GET.get("q", "").strip()
    zone = request.GET.get("zone", "").strip()
    hometown = request.GET.get("hometown", "").strip()[:120]
    name_status = request.GET.get("name_status", "").strip()
    data_status = request.GET.get("data_status", "").strip()
    records = Martyr.objects.all()
    if query:
        normalized = normalize(query)
        records = records.filter(Q(normalized_name__icontains=normalized) | Q(hometown__icontains=query) | Q(grave_number__iexact=query))
    if zone:
        records = records.filter(zone=zone)
    if hometown:
        records = records.filter(hometown__icontains=hometown)
    if name_status == "known":
        records = records.exclude(name="")
    elif name_status == "unknown":
        records = records.filter(name="")
    if data_status == "birth":
        records = records.exclude(birth_text="")
    elif data_status == "death":
        records = records.exclude(death_text="")
    elif data_status == "both_dates":
        records = records.exclude(birth_text="").exclude(death_text="")
    elif data_status == "position":
        records = records.exclude(zone="").exclude(grave_row="").exclude(grave_number="")
    elif data_status == "incomplete":
        records = records.filter(Q(name="") | Q(hometown="") | Q(birth_text="") | Q(death_text="") | Q(zone="") | Q(grave_row="") | Q(grave_number=""))
    return records, query, zone, hometown, name_status, data_status


def home(request):
    records = Martyr.objects.all()
    total = records.count()
    complete_records = records.exclude(name="").exclude(hometown="").exclude(
        birth_text=""
    ).exclude(death_text="").exclude(zone="").exclude(grave_row="").exclude(grave_number="")
    zones = Martyr.objects.exclude(zone="").values_list("zone", flat=True).distinct().order_by("zone")
    return render(request, "memorial/home.html", {
        "featured_martyrs": complete_records.order_by("?")[:8], "zones": zones, "total": total,
        "total_display": f"{total:,}".replace(",", "."), "home_images": _home_image_urls(),
    })


@require_POST
@user_passes_test(lambda user: user.is_active and user.is_superuser, login_url="/admin/login/")
def replace_home_image(request):
    key = request.POST.get("key", "")
    image_file = request.FILES.get("image")
    if key not in HOME_IMAGE_SLOTS or not image_file:
        messages.error(request, "Vị trí ảnh hoặc tệp tải lên không hợp lệ.")
        return redirect("home")
    if image_file.size > 25 * 1024 * 1024:
        messages.error(request, "Ảnh vượt quá dung lượng tối đa 25 MB.")
        return redirect("home")
    if image_file.content_type not in {"image/jpeg", "image/png", "image/webp"}:
        messages.error(request, "Chỉ hỗ trợ ảnh JPG, PNG hoặc WebP.")
        return redirect("home")

    anchor, max_width, background = HOME_IMAGE_SLOTS[key]
    try:
        Image.MAX_IMAGE_PIXELS = 40_000_000
        image_file.seek(0)
        with Image.open(image_file) as source:
            source.verify()
        image_file.seek(0)
        with Image.open(image_file) as source:
            image = ImageOps.exif_transpose(source)
            image.thumbnail((max_width, max_width), Image.Resampling.LANCZOS)
            if image.mode in {"RGBA", "LA"}:
                canvas = Image.new("RGB", image.size, background)
                canvas.paste(image, mask=image.getchannel("A"))
                image = canvas
            elif image.mode != "RGB":
                image = image.convert("RGB")
            output = BytesIO()
            image.save(output, "WEBP", quality=88, method=6)
    except (UnidentifiedImageError, OSError, ValueError, Image.DecompressionBombError):
        messages.error(request, "Không thể đọc ảnh này hoặc ảnh có kích thước không an toàn.")
        return redirect("home")

    payload = output.getvalue()
    targets = [Path(settings.BASE_DIR) / "static" / "uploads" / "home", Path(settings.STATIC_ROOT) / "uploads" / "home"]
    for directory in targets:
        directory.mkdir(parents=True, exist_ok=True)
        temporary = directory / f".{key}.{os.getpid()}.tmp"
        temporary.write_bytes(payload)
        os.replace(temporary, directory / f"{key}.webp")
    messages.success(request, "Ảnh đã được thay và hiển thị trên trang chủ.")
    return redirect(f"/#{anchor}")


def martyr_list(request):
    records, query, zone, hometown, name_status, data_status = _filtered_records(request)
    page = Paginator(records, 24).get_page(request.GET.get("page"))
    zones = Martyr.objects.exclude(zone="").values_list("zone", flat=True).distinct().order_by("zone")
    pagination_params = request.GET.copy()
    pagination_params.pop("page", None)
    active_filter_count = sum(bool(value) for value in (hometown, name_status, data_status))
    total = Martyr.objects.count()
    return render(request, "memorial/martyr_list.html", {
        "page": page, "query": query, "zone": zone, "zones": zones,
        "hometown": hometown, "name_status": name_status, "data_status": data_status,
        "active_filter_count": active_filter_count,
        "advanced_open": active_filter_count > 0,
        "pagination_query": pagination_params.urlencode(),
        "total": total, "total_display": f"{total:,}".replace(",", "."),
    })

def suggestions(request):
    query = request.GET.get("q", "").strip()[:80]
    if len(query) < 2:
        return JsonResponse({"results": []})
    normalized = normalize(query)
    matches = Martyr.objects.filter(
        Q(normalized_name__icontains=normalized) | Q(hometown__icontains=query) | Q(grave_number__iexact=query)
    ).annotate(search_rank=Case(
        When(normalized_name=normalized, then=Value(0)),
        When(normalized_name__startswith=normalized, then=Value(1)),
        When(normalized_name__icontains=normalized, then=Value(2)),
        When(hometown__icontains=query, then=Value(3)),
        When(grave_number__iexact=query, then=Value(4)),
        default=Value(5), output_field=IntegerField(),
    )).order_by("search_rank", "name", "source_id").values(
        "source_id", "name", "hometown", "zone", "grave_row", "grave_number"
    )[:8]
    results = [{**item, "name": item["name"] or "Chưa biết tên", "url": f"/liet-si/{item['source_id']}/"} for item in matches]
    response = JsonResponse({"results": results})
    response["Cache-Control"] = "private, max-age=60"
    return response

def detail(request, source_id):
    martyr = get_object_or_404(Martyr, source_id=source_id)
    family_form = FamilyConnectionForm(initial={"started_at": signing.dumps(time.time(), salt="family-form")})
    form = TributeForm(initial={"started_at": signing.dumps(time.time(), salt="tribute-form")})
    if request.method == "POST" and request.POST.get("form_action") == "family_connection":
        family_form = FamilyConnectionForm(request.POST, request.FILES)
        if family_form.is_valid():
            try:
                started = signing.loads(family_form.cleaned_data["started_at"], salt="family-form", max_age=7200)
            except signing.BadSignature:
                family_form.add_error(None, "Phiên gửi thông tin không hợp lệ. Vui lòng tải lại trang.")
            else:
                ip = request.META.get("HTTP_X_FORWARDED_FOR", "").split(",")[-1].strip() or request.META.get("REMOTE_ADDR", "")
                ip_hash = hashlib.sha256(f"{settings.SECRET_KEY}:{ip}".encode()).hexdigest()
                recent = timezone.now() - timedelta(days=1)
                is_bot = bool(family_form.cleaned_data["website"]) or time.time() - float(started) < 4
                too_many = FamilySubmission.objects.filter(ip_hash=ip_hash, created_at__gte=recent).count() >= 2
                if is_bot:
                    family_form.add_error(None, "Không thể xác minh thao tác. Vui lòng thử lại.")
                elif too_many:
                    family_form.add_error(None, "Bạn đã gửi thông tin trong thời gian gần đây. Ban quản trị sẽ sớm liên hệ xác minh.")
                else:
                    FamilySubmission.objects.create(
                        martyr=martyr,
                        full_name=family_form.cleaned_data["full_name"],
                        relationship=family_form.cleaned_data["relationship"],
                        phone=family_form.cleaned_data["phone"],
                        email=family_form.cleaned_data["email"],
                        hometown=family_form.cleaned_data["hometown"],
                        message=family_form.cleaned_data["message"],
                        evidence=family_form.cleaned_data.get("evidence"),
                        allow_publication=family_form.cleaned_data["allow_publication"],
                        consented_at=timezone.now(), ip_hash=ip_hash,
                        user_agent=request.META.get("HTTP_USER_AGENT", "")[:300],
                    )
                    messages.success(request, "Thông tin thân nhân đã được tiếp nhận riêng tư. Ban quản trị sẽ liên hệ sau khi đối chiếu hồ sơ.")
                    return redirect(f"/liet-si/{source_id}/#ket-noi-than-nhan")
    elif request.method == "POST":
        form = TributeForm(request.POST)
        if form.is_valid():
            try:
                started = signing.loads(form.cleaned_data["started_at"], salt="tribute-form", max_age=7200)
            except signing.BadSignature:
                form.add_error(None, "Phiên gửi lời tri ân không hợp lệ. Vui lòng tải lại trang.")
            else:
                # Nginx appends the real peer address to X-Forwarded-For; use the
                # last value so a client-supplied first value cannot evade limits.
                ip = request.META.get("HTTP_X_FORWARDED_FOR", "").split(",")[-1].strip() or request.META.get("REMOTE_ADDR", "")
                ip_hash = hashlib.sha256(f"{settings.SECRET_KEY}:{ip}".encode()).hexdigest()
                recent = timezone.now() - timedelta(hours=1)
                duplicate_since = timezone.now() - timedelta(days=1)
                is_bot = bool(form.cleaned_data["website"]) or time.time() - float(started) < 3
                too_many = Tribute.objects.filter(ip_hash=ip_hash, created_at__gte=recent).count() >= 3
                duplicate = Tribute.objects.filter(
                    ip_hash=ip_hash, martyr=martyr, content=form.cleaned_data["content"], created_at__gte=duplicate_since
                ).exists()
                if is_bot:
                    form.add_error(None, "Không thể xác minh thao tác. Vui lòng thử lại.")
                elif too_many:
                    form.add_error(None, "Bạn đã gửi nhiều lời tri ân trong thời gian ngắn. Vui lòng thử lại sau.")
                elif duplicate:
                    form.add_error(None, "Lời tri ân này đã được gửi trước đó.")
                else:
                    Tribute.objects.create(
                        martyr=martyr, author_name=form.cleaned_data["author_name"], phone=form.cleaned_data["phone"],
                        content=form.cleaned_data["content"], ip_hash=ip_hash,
                        user_agent=request.META.get("HTTP_USER_AGENT", "")[:300],
                    )
                    messages.success(request, "Lời tri ân đã được ghi nhận và sẽ hiển thị sau khi được kiểm duyệt. Xin cảm ơn bạn.")
                    return redirect(f"/liet-si/{source_id}/#loi-tri-an")
    tributes = martyr.tributes.filter(status=Tribute.Status.APPROVED)[:20]
    return render(request, "memorial/detail.html", {
        "martyr": martyr, "tribute_form": form, "family_form": family_form, "tributes": tributes,
        "family_verified": martyr.family_submissions.filter(status=FamilySubmission.Status.VERIFIED).exists(),
        "editorial_tributes": generated_memorial_messages(martyr),
    })

def tour(request):
    return render(request, "memorial/tour.html", {
        "tour_configuration": TourConfiguration.load(),
        "tour_points": TourPoint.objects.filter(is_active=True),
    })


def tour_overview_image(request):
    configuration = TourConfiguration.load()
    if configuration.overview_image:
        try:
            return FileResponse(configuration.overview_image.open("rb"), content_type=mimetypes.guess_type(configuration.overview_image.name)[0] or "image/jpeg")
        except (FileNotFoundError, OSError):
            pass
    fallback = Path(settings.BASE_DIR) / "static" / "images" / "nghia-trang-viet-lao-panorama-360.jpg"
    return FileResponse(fallback.open("rb"), content_type="image/jpeg")


def tour_zone_map(request, zone):
    records = Martyr.objects.filter(zone=zone).order_by("grave_row", "grave_number", "name", "source_id")
    results = [{
        "id": record.source_id, "name": record.name or "Chưa rõ tên",
        "row": record.grave_row, "number": record.grave_number,
        "url": f"/liet-si/{record.source_id}/",
    } for record in records]
    positioned = sum(bool(item["row"] and item["number"] and item["row"] != "0" and item["number"] != "0") for item in results)
    return JsonResponse({"zone": zone, "count": len(results), "positioned": positioned, "results": results})


@staff_member_required(login_url="/admin/login/")
@require_http_methods(["GET", "POST"])
def tour_manager(request):
    configuration = TourConfiguration.load()
    if request.method == "POST":
        action = request.POST.get("action", "")
        if action == "upload":
            upload = request.FILES.get("overview_image")
            if not upload or upload.content_type not in {"image/jpeg", "image/png", "image/webp"} or upload.size > 25 * 1024 * 1024:
                messages.error(request, "Ảnh không hợp lệ. Chỉ nhận JPG, PNG, WebP tối đa 25 MB.")
            else:
                configuration.overview_image.save(upload.name, upload, save=True)
                messages.success(request, "Đã cập nhật ảnh tổng quan.")
            return redirect("tour_manager")
        if action == "positions":
            try:
                points = json.loads(request.POST.get("points", "[]"))
                for item in points:
                    TourPoint.objects.filter(slug=item["slug"]).update(
                        x_percent=max(0, min(100, float(item["x"]))),
                        y_percent=max(0, min(100, float(item["y"]))),
                    )
                return JsonResponse({"ok": True})
            except (TypeError, ValueError, KeyError, json.JSONDecodeError):
                return JsonResponse({"ok": False, "error": "Tọa độ không hợp lệ."}, status=400)
        if action == "point_save":
            try:
                point_id = request.POST.get("point_id")
                point = get_object_or_404(TourPoint, pk=point_id) if point_id else TourPoint()
                point.number = max(1, min(99, int(request.POST.get("number", "1"))))
                point.title = request.POST.get("title", "").strip()[:120]
                if not point.title:
                    raise ValueError
                point.slug = point.slug or re.sub(r"[^a-z0-9]+", "-", normalize(point.title)).strip("-") or f"diem-{point.number}"
                point.description = request.POST.get("description", "").strip()
                point.is_active = request.POST.get("is_active") == "on"
                point.save()
                return JsonResponse({"ok": True, "id": point.pk})
            except (ValueError, TypeError):
                return JsonResponse({"ok": False, "error": "Thông tin điểm chưa hợp lệ."}, status=400)
        if action == "point_delete":
            deleted, _ = TourPoint.objects.filter(pk=request.POST.get("point_id")).delete()
            return JsonResponse({"ok": bool(deleted)}, status=200 if deleted else 404)
        return JsonResponse({"ok": False, "error": "Thao tác không hợp lệ."}, status=400)
    return render(request, "memorial/tour_manager.html", {
        "tour_configuration": configuration,
        "tour_points": TourPoint.objects.all(),
    })

def about(request):
    return redirect("/#cau-chuyen-home", permanent=True)

def health(request):
    response = JsonResponse({"status": "ok"})
    response["X-Robots-Tag"] = "noindex, nofollow"
    return response

def robots(request):
    content = "User-agent: *\nAllow: /\nDisallow: /admin/\nDisallow: /api/\nDisallow: /health/\nSitemap: https://lietsivietlao.8tech.vn/sitemap.xml\n"
    return HttpResponse(content, content_type="text/plain; charset=utf-8")

def sitemap(request):
    urls = [("https://lietsivietlao.8tech.vn/", "daily", "1.0"), ("https://lietsivietlao.8tech.vn/danh-sach-liet-si/", "daily", "0.9"), ("https://lietsivietlao.8tech.vn/trai-nghiem-360/", "weekly", "0.8")]
    urls.extend((f"https://lietsivietlao.8tech.vn/liet-si/{source_id}/", "monthly", "0.7") for source_id in Martyr.objects.values_list("source_id", flat=True).iterator())
    items = "".join(f"<url><loc>{url}</loc><changefreq>{frequency}</changefreq><priority>{priority}</priority></url>" for url, frequency, priority in urls)
    xml = '<?xml version="1.0" encoding="UTF-8"?><urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">' + items + "</urlset>"
    response = HttpResponse(xml, content_type="application/xml; charset=utf-8")
    response["Cache-Control"] = "public, max-age=21600"
    return response
