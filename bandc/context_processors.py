def base_url(request):
    return {"BASE_URL": request.build_absolute_uri("/").rstrip("/")}
