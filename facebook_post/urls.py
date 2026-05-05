from django.urls import path
from .views import (
    SchedulePostView,
    ScheduledPostListView,
    ScheduledPostDetailView,
    CancelScheduledPostView,
)

urlpatterns = [
    path("facebook/schedule/", SchedulePostView.as_view()),
    path("facebook/schedule/list/", ScheduledPostListView.as_view()),
    path("facebook/schedule/<int:post_id>/", ScheduledPostDetailView.as_view()),
    path("facebook/schedule/<int:post_id>/cancel/", CancelScheduledPostView.as_view()),
]