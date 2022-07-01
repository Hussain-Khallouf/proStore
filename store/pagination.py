from rest_framework.pagination import PageNumberPagination


class StanderedPagenation(PageNumberPagination):
    page_size = 5
