from datetime import datetime
from django.views.generic.list import ListView
from django.views.generic.detail import DetailView
from django.views.generic.edit import CreateView, UpdateView, DeleteView
from accounts.models import User
from blog.models import Post
from taggit.models import Tag
from django.contrib.auth.decorators import user_passes_test
from django.utils.decorators import method_decorator
from django.utils.text import slugify
from django.core.urlresolvers import reverse_lazy


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


class SuperuserRequiredMixin(object):
    @method_decorator(user_passes_test(lambda u: u.is_superuser))
    def dispatch(self, *args, **kwargs):
        return super(SuperuserRequiredMixin, self).dispatch(*args, **kwargs)


class PostAdminListView(SuperuserRequiredMixin, ListView):
    model = Post
    template_name = "blog/admin_list.html"
    context_object_name = 'posts'

    def get_context_data(self, **kwargs):
        context = super(PostAdminListView, self).get_context_data(**kwargs);
        print context
        context['initial_post'] = context['posts'].first()
        return context;


class PostPreviewView(DetailView):
    model = Post
    context_object_name = 'post'
    template_name = 'blog/post_preview.html'


class BlogPostCreateView(SuperuserRequiredMixin, CreateView):
    model = Post
    template_name = "blog/post_form.html"
    fields = ('title', 'content', 'tags')
    success_url = reverse_lazy('blog_admin')

    def form_valid(self, form):
        form.instance.author = self.request.user
        form.instance.slug = slugify(form.instance.title)
        return super(BlogPostCreateView, self).form_valid(form)


class BlogPostEditView(SuperuserRequiredMixin, UpdateView):
    model = Post
    template_name = "blog/post_form.html"
    fields = ('title', 'content', 'tags')
    success_url = reverse_lazy('blog_admin')

    def form_valid(self, form):
        form.instance.slug = slugify(form.instance.title)
        return super(BlogPostEditView, self).form_valid(form)


class DeleteBlogPost(SuperuserRequiredMixin, DeleteView):
    model = Post
    success_url = reverse_lazy('blog_admin')