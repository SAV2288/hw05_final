from django.db import models
from django.contrib.auth import get_user_model


User = get_user_model()


# Модель сообщества
class Group(models.Model):
    title = models.CharField(max_length=200)
    slug = models.SlugField(null=False, unique=True)
    description = models.TextField()

    def __str__(self):
       # выводим название группы
       return self.title


# Модель публикации
class Post(models.Model):           
    text = models.TextField()
    pub_date = models.DateTimeField("date published", auto_now_add=True)
    author = models.ForeignKey(User, on_delete=models.CASCADE, related_name="author_post")
    group = models.ForeignKey(Group, on_delete=models.CASCADE, related_name="group_posts", blank=True, null=True)
    image = models.ImageField(upload_to='posts/', blank=True, null=True)

    def __str__(self):
       # выводим текст поста 
       return self.text

# Модель коментария
class Comment(models.Model):
    post = models.ForeignKey(Post, on_delete=models.CASCADE, related_name="post_comment")
    author = models.ForeignKey(User, on_delete=models.CASCADE, related_name="author_comment")
    text = models.TextField()
    created = models.DateTimeField("date published", auto_now_add=True)


class Follow(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="follower")
    author = models.ForeignKey( User, on_delete=models.CASCADE, related_name="following")