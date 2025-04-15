from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    FileUploadView,
    FileListView,
    FileDownloadView,
    FileDeleteView,
    FileRenameView,
    FileUpdateCommentView,
    FilePublicLinkView,
    FileDownloadByLinkView,
    FolderViewSet
)

app_name = 'cloud'

router = DefaultRouter()
router.register(r'folders', FolderViewSet, basename='folder')

urlpatterns = [
    path('files/upload/', FileUploadView.as_view(), name='file-upload'),
    path('files/', FileListView.as_view(), name='file-list'),
    path('files/<int:pk>/download/', FileDownloadView.as_view(), name='file-download'),
    path('files/<int:pk>/delete/', FileDeleteView.as_view(), name='file-delete'),
    path('files/<int:pk>/rename/', FileRenameView.as_view(), name='file-rename'),
    path('files/<int:pk>/comment/', FileUpdateCommentView.as_view(), name='file-update-comment'),
    path('files/<int:pk>/public-link/', FilePublicLinkView.as_view(), name='file-public-link'),

    path('public/files/<uuid:public_link>/download/', FileDownloadByLinkView.as_view(), name='file-download-by-link'),
    
    path('', include(router.urls)),
]
