from rest_framework.pagination import PageNumberPagination

class Pagination(PageNumberPagination):
    page_size = 10  # 페이지당 10개의 결과를 보여줌