from django.db import models


class SearchTrend(models.Model):

    query_key = models.CharField(
        max_length=255,
        unique=True
    )

    display_query = models.CharField(
        max_length=255
    )

    search_count = models.PositiveIntegerField(default=0)

    last_searched = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.display_query