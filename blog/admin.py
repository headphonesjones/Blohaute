from django.contrib import admin
from blog.models import Post, PostImage

admin.site.register(Post)
admin.site.register(PostImage)