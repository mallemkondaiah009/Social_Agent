from django.urls import path
from .views import (
    GeneratePostView,
    ScheduleAdView,
    SchedulePostView,
    ScheduledPostListView,
    ScheduledPostDetailView,
    CancelScheduledPostView,
)

urlpatterns = [
    path("meta/ads/schedule/", ScheduleAdView.as_view()),
    path("facebook/posts/schedule/", GeneratePostView.as_view()),
    path("facebook/schedule/", SchedulePostView.as_view()),
    path("facebook/schedule/list/", ScheduledPostListView.as_view()),
    path("facebook/schedule/<int:post_id>/", ScheduledPostDetailView.as_view()),
    path("facebook/schedule/<int:post_id>/cancel/", CancelScheduledPostView.as_view()),
]
