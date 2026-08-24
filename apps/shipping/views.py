from django.http import JsonResponse

from apps.shipping.novaposhta import get_branches, search_cities


def cities(request):
    return JsonResponse({"results": search_cities(request.GET.get("q", ""))})


def branches(request):
    return JsonResponse({"results": get_branches(request.GET.get("city_ref", ""))})
