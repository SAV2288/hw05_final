from django import forms
from .models import Post, Comment

# Класс формы новой записи
class NewPost(forms.ModelForm):
    class Meta():
        # Модель, с которой связана создаваемая форма
        model = Post
        # Поля, которые должны быть видны в форме и в каком порядке
        fields = ("text", "group", "image")
        

class CommentForm(forms.ModelForm):
    text = forms.CharField( widget=forms.Textarea(attrs={"rows":5, "cols":20}))
    class Meta():
        model = Comment
        fields = ("text",)
