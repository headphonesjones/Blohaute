from django.core.urlresolvers import reverse
from django.db import models
from accounts.models import User
from taggit.managers import TaggableManager

class Post(models.Model):
    title = models.CharField(max_length=255)
    slug = models.SlugField(max_length=255)
    author = models.ForeignKey(User)
    content = models.TextField()
    image = models.ImageField(upload_to='blog/images/%Y/%m/%d', blank=True)
    publication_date = models.DateTimeField(auto_now_add=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    tags = TaggableManager(blank=True)

    class Meta:
        ordering = ('-publication_date', )

    def __unicode__(self):
        return self.title

    def get_absolute_url(self):
        return reverse('blog_post', kwargs={'slug': self.slug})


class PostImage(models.Model):
    image = models.ImageField(upload_to='blog/images/%Y/%m/%d', blank=True)
    post = models.ForeignKey(Post, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __unicode__(self):
        return self.image.url
