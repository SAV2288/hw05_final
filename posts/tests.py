from django.shortcuts import get_object_or_404
from django.contrib.auth import get_user_model
from django.test import TestCase, Client
from .models import Post, Group, Follow

User = get_user_model()


class YatubeTest(TestCase):
    def setUp(self):
        self.client = Client()
        # регистрация пользователей
        self.client.post(
            "/auth/signup/",
            {"username": "testUser", "password1": "fjvndyb5248", "password2": "fjvndyb5248"},
            )
        
        self.client.post(
            "/auth/signup/",
            {"username": "testUser2", "password1": "dgfhh586hr", "password2": "dgfhh586hr"},
            )


    # После регистрации пользователя создается его персональная страница (profile)
    def testUserProfile(self):
        response = self.client.get("/testUser/")
        self.assertEqual(response.status_code, 200)

    
    # Авторизованный пользователь может опубликовать пост (new)
    def testUserCreateNewPost(self):
        # Авторизация пользователя и создание поста
        self.client.login(username="testUser", password="fjvndyb5248")
        self.client.post("/new/", {"text": "Тестовый пост"})
        # Проверка наличия постов у пользователя
        authorPost = User.objects.get(username="testUser")
        post = Post.objects.filter(author=authorPost.pk).count()
        self.assertTrue(post)


    # Неавторизованный посетитель не может опубликовать пост (его редиректит на страницу входа)
    def testNoAuthUserCreateNewPost(self):
        response = self.client.post("/new/", {"text": "Тестовый пост"}, follow=True)
        self.assertEqual(response.redirect_chain, [("/auth/login/?next=/new/", 302)])


    # После публикации поста новая запись появляется на главной странице сайта (index),
    # на персональной странице пользователя (profile), и на отдельной странице поста (post)
    def testVisibilityNewPost(self):
        # Авторизация пользователя и создание поста
        self.client.login(username="testUser", password="fjvndyb5248")
        self.client.post("/new/", {"text": "Тестовый пост"})
        # Проверка наличия поста:
        # на главной странице
        response = self.client.get("")
        self.assertContains(response, "Тестовый пост", count=None, status_code=200, msg_prefix='', html=False)
        # в профайле пользователя
        response = self.client.get("/testUser/")
        self.assertContains(response, "Тестовый пост", count=None, status_code=200, msg_prefix='', html=False)
        # на странице поста
        post = Post.objects.get(text="Тестовый пост")
        response = self.client.get(f"/testUser/{post.pk}/")
        self.assertContains(response, "Тестовый пост", count=None, status_code=200, msg_prefix='', html=False)


    # Авторизованный пользователь может отредактировать свой пост и его содержимое изменится на всех связанных страницах
    def testUserUpdatePost(self):
        # Авторизация пользователя и создание поста
        self.client.login(username="testUser", password="fjvndyb5248")
        self.client.post("/new/", {"text": "Тестовый пост"})
        # Изменение поста
        post = Post.objects.get(text="Тестовый пост")
        self.client.post(f"/testUser/{post.pk}/edit/", {"text": "Новое содержимое поста"})
        # Проверка изменений
        response = self.client.get(f"/testUser/{post.pk}/")
        self.assertContains(response, "Новое содержимое поста", count=None, status_code=200, msg_prefix='', html=False)


    # Не авторизованный пользователь не может отредактировать пост (его редиректит на страницу поста)
    def testNoAuthUserUpdatePost(self):
        # Авторизация пользователя, создание поста и выход
        self.client.login(username="testUser", password="fjvndyb5248")
        self.client.post("/new/", {"text": "Тестовый пост"})
        self.client.logout()
        # Попытка изменить пост
        post = Post.objects.get(text="Тестовый пост")
        response = self.client.post(f"/testUser/{post.pk}/edit/", {"text": "Новое содержимое поста"}, follow=True)
        # Проверка редиректа
        self.assertEqual(response.redirect_chain, [(f"/testUser/{post.pk}/", 302)])
        # Проверка поста на отсутствие изменений
        response = self.client.get(f"/testUser/{post.pk}/")
        self.assertNotContains(response, "Новое содержимое поста", status_code=200, msg_prefix='', html=False)
        self.assertContains(response, "Тестовый пост", count=None, status_code=200, msg_prefix='', html=False)

    
    # Авторизованный пользователь не может отредактировать чужей пост (его редиректит на страницу поста)
    def testUserUpdateSomeoneElsesPost(self):
        # Авторизация пользователя, создание поста и выход
        self.client.login(username="testUser", password="fjvndyb5248")
        self.client.post("/new/", {"text": "Тестовый пост"})
        self.client.logout()
        # Авторизация другого пользователя и попытка изменить пост
        self.client.login(username="testUser2", password="dgfhh586hr")
        post = Post.objects.get(text="Тестовый пост")
        response = self.client.post(f"/testUser/{post.pk}/edit/", {"text": "Новое содержимое поста"}, follow=True)
        # Проверка редиректа
        self.assertEqual(response.redirect_chain, [(f"/testUser/{post.pk}/", 302)])
        # Проверка поста на отсутствие изменений
        response = self.client.get(f"/testUser/{post.pk}/")
        self.assertNotContains(response, "Новое содержимое поста", status_code=200, msg_prefix='', html=False)
        self.assertContains(response, "Тестовый пост", count=None, status_code=200, msg_prefix='', html=False)


    # Тест ошибки 404
    def testError404(self):
        response = self.client.get("/which_page_does_not_exist/")
        self.assertEqual(response.status_code, 404)


    # Тест наличия тега <img на страницах с постами
    def testPostImgTag(self):
        self.client.login(username="testUser", password="fjvndyb5248")
        self.group = Group.objects.create(pk=1, title="test_group", slug="test_group", description="description")
        with open("media/posts/12st.jpg","rb") as img:
            self.client.post("/new/", {"text": "Тестовый пост", "image": img, "group": 1})
        
        response = self.client.get("/")
        self.assertContains(response, "<img", count=None, status_code=200, msg_prefix='', html=False)

        post = Post.objects.get(text="Тестовый пост")
        response = self.client.get(f"/testUser/{post.pk}/")
        self.assertContains(response, "<img", count=None, status_code=200, msg_prefix='', html=False)

        response = self.client.get("/testUser/")
        self.assertContains(response, "<img", count=None, status_code=200, msg_prefix='', html=False)

        response = self.client.get("/group/test_group/")
        self.assertContains(response, "<img", count=None, status_code=200, msg_prefix='', html=False)


    # Тест ошибку при загрузке не картинки
    def testNoImgFormat(self):
        self.client.login(username="testUser", password="fjvndyb5248")
        with open("media/posts/test_file.txt","rb") as img:
            self.client.post("/new/", {"text": "Тестовый пост", "image": img})

        post = Post.objects.filter(text="Тестовый пост")
        self.assertEqual(len(post), 0)
    

    # Тест на проверку кеширования главной страницы
    def testIndexPageCache(self):
        # Авторизация пользователя и создание поста
        self.client.login(username="testUser", password="fjvndyb5248")
        self.client.post("/new/", {"text": "Тестовый пост"})
        # Проверка наличия поста:
        # на главной странице
        response = self.client.get("")
        self.assertContains(response, "Тестовый пост", count=None, status_code=200, msg_prefix='', html=False)
        # на странице поста
        post = Post.objects.get(text="Тестовый пост")
        response = self.client.get(f"/testUser/{post.pk}/")
        self.assertContains(response, "Тестовый пост", count=None, status_code=200, msg_prefix='', html=False)
        # Изменение поста
        post = Post.objects.get(text="Тестовый пост")
        self.client.post(f"/testUser/{post.pk}/edit/", {"text": "Новое содержимое поста"})
        # Проверка изменений на странице поста
        response = self.client.get(f"/testUser/{post.pk}/")
        self.assertContains(response, "Новое содержимое поста", count=None, status_code=200, msg_prefix='', html=False)
        # Проверка отсутствия изменений на главной странице
        response = self.client.get("")
        self.assertNotContains(response, "Новое содержимое поста", status_code=200, msg_prefix='', html=False)


    # Авторизованный пользователь может подписаться на автора и отписаться от него
    def testFollow(self):
        testUser = get_object_or_404(User, username="testUser")
        testUser2 = get_object_or_404(User, username="testUser2")

        self.client.login(username="testUser", password="fjvndyb5248")

        self.client.get("/testUser2/follow")
        follow = Follow.objects.get(user=testUser, author=testUser2)
        self.assertTrue(follow)

        self.client.get("/testUser2/unfollow")
        follow = Follow.objects.filter(user=testUser, author=testUser2)
        self.assertFalse(follow)


    # Новая запись пользователя появляется в ленте тех, кто на него подписан
    # и не появляется в ленте тех, кто не подписан на него
    def testFollowIndex(self):
        self.client.login(username="testUser", password="fjvndyb5248")
        self.client.post("/new/", {"text": "Тестовый пост"})
        self.client.logout()

        self.client.login(username="testUser2", password="dgfhh586hr")

        self.client.get("/testUser/follow")
        response = self.client.get("/follow/")
        self.assertContains(response, "Тестовый пост", count=None, status_code=200, msg_prefix='', html=False)

        self.client.get("/testUser/unfollow")
        response = self.client.get("/follow/")
        self.assertNotContains(response, "Тестовый пост", status_code=200, msg_prefix='', html=False)


    # Только авторизированный пользователь может комментировать посты
    def testComment(self):
        self.client.login(username="testUser", password="fjvndyb5248")
        self.client.post("/new/", {"text": "Тестовый пост"})
        post = Post.objects.get(text="Тестовый пост")
        self.client.logout()

        self.client.login(username="testUser2", password="dgfhh586hr")

        self.client.post(f"/testUser/{post.pk}/comment/", {"text": "Тестовый комментарий"})
        response = self.client.get(f"/testUser/{post.pk}/")
        self.assertContains(response, "Тестовый комментарий", count=None, status_code=200, msg_prefix='', html=False)

        self.client.logout()

        self.client.post(f"/testUser/{post.pk}/comment/", {"text": "Еще один комментарий"})
        response = self.client.get(f"/testUser/{post.pk}/")
        self.assertNotContains(response, "Еще один комментарий", status_code=200, msg_prefix='', html=False)
