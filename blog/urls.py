from django.conf.urls import patterns, url, include
from blog.views import PostListView, PostDetailView, AuthorPostListView, TagPostListView, BlogPostEditView, BlogPostCreateView

urlpatterns = patterns(
    '',
    url(r'^$', PostListView.as_view(), name='post_list'),
    url(r'^admin/$', BlogPostEditView.as_view(), name='admin'),
    url(r'^admin/create/$', BlogPostCreateView.as_view(), name='create_post'),
    url(r'^admin/edit/(?P<pk>\d+)/$', BlogPostEditView.as_view(), name='edit_post'),
    url(r'^author/(?P<pk>\d+)/$', AuthorPostListView.as_view(), name="author_post_list"),
    url(r'^tag/(?P<tag>[\w-]+)/$', TagPostListView.as_view(), name="tag_post_list"),
    url(r'^(?P<slug>[\w-]+)/$', PostDetailView.as_view(), name='blog_post'),

)
