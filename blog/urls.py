from django.conf.urls import patterns, url
from blog import views


urlpatterns = patterns(
    '',
    url(r'^$', views.PostListView.as_view(), name='post_list'),
    url(r'^admin/$', views.PostAdminListView.as_view(), name='blog_admin'),
    url(r'^admin/create/$', views.BlogPostCreateView.as_view(), name='create_post'),
    url(r'^admin/edit/(?P<pk>\d+)/$', views.BlogPostEditView.as_view(), name='edit_post'),
    url(r'^admin/delete/(?P<pk>\d+)/$', views.DeleteBlogPost.as_view(), name='delete_post'),
    url(r'^admin/image_upload/$', views.PostImageUploader.as_view(), name="upload_blog_image"),
    url(r'^admin/image_link/(?P<pk>\d+)/$', views.PostImageLink.as_view(), name="blog_image_link"),
    url(r'^author/(?P<pk>\d+)/$', views.AuthorPostListView.as_view(), name="author_post_list"),
    url(r'^tag/(?P<tag>[\w-]+)/$', views.TagPostListView.as_view(), name="tag_post_list"),
    url(r'^(?P<slug>[\w-]+)/$', views.PostDetailView.as_view(), name='blog_post'),
    url(r'^(?P<slug>[\w-]+)/preview/$', views.PostPreviewView.as_view(), name='blog_post_preview'),
)
