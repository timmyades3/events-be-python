from django.urls import path


from . import views


urlpatterns = [
    path("<str:event_id>/comment/", views.CommentListAPIView.as_view()),
    path("<str:event_id>/comments/", views.CommentListAPIView.as_view()),
]
