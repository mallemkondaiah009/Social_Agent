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
    path("meta/ads/generate-schedule/", ScheduleAdView.as_view()),
    path("facebook/posts/generate-schedule/", GeneratePostView.as_view()),
    path("facebook/normal-schedule/", SchedulePostView.as_view()),
    path("facebook/scheduled-posts/list/", ScheduledPostListView.as_view()),
    path("facebook/scheduled-post/<int:post_id>/", ScheduledPostDetailView.as_view()),
    path("facebook/scheduled-post/<int:post_id>/cancel/", CancelScheduledPostView.as_view()),
]
