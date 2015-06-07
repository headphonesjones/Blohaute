from datetime import datetime
from django.views.generic.list import ListView
from django.views.generic.detail import DetailView
from django.views.generic.edit import CreateView, UpdateView
from accounts.models import User
from blog.models import Post
from taggit.models import Tag


class PostListView(ListView):
    queryset = Post.objects.filter(publication_date__lte=datetime.now())
    context_object_name = 'posts'


class AuthorPostListView(PostListView):
    def get_queryset(self):
        queryset = super(AuthorPostListView, self).get_queryset()
        return queryset.filter(author_id=self.kwargs['pk'])

    def get_context_data(self, *args, **kwargs):
        context = super(AuthorPostListView, self).get_context_data(*args, **kwargs)
        context['subtitle'] = User.objects.get(pk=self.kwargs['pk']).get_full_name()
        return context


class TagPostListView(PostListView):
    def get_queryset(self):
        queryset = super(TagPostListView, self).get_queryset()

        return queryset.filter(tags__slug__in=[self.kwargs['tag']])

    def get_context_data(self, *args, **kwargs):
        context = super(TagPostListView, self).get_context_data(*args, **kwargs)
        context['subtitle'] = Tag.objects.get(slug=self.kwargs['tag']).name
        return context


class PostDetailView(DetailView):
    model = Post
    context_object_name = 'post'


class BlogPostCreateView(CreateView):
    model = Post
    template_name = "blog/post_form.html"
    fields = ('title', 'content')


class BlogPostEditView(UpdateView):
    model = Post
    template_name = "blog/post_form.html"
    fields = ('title', 'content', 'tags')
